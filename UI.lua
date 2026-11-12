-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
local function button(parent,label,w,x,y,callback)
    local b=CreateFrame("Button",nil,parent,"UIPanelButtonTemplate")
    b:SetSize(w,24); b:SetPoint("TOPLEFT",x,y); b:SetText(label); b:SetScript("OnClick",callback)
    return b
end
function ns.CreateUI()
    if ns.frame then return end
    local f=CreateFrame("Frame","ProfessionGuideFrame",UIParent,"BackdropTemplate")
    ns.frame=f; f:SetSize(660,620); f:SetPoint("CENTER"); f:SetClampedToScreen(true)
    f:SetMovable(true); f:EnableMouse(true); f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart",function(self) self:StartMoving() end)
    f:SetScript("OnDragStop",function(self)
        self:StopMovingOrSizing()
        local point,_,relativePoint,x,y=self:GetPoint()
        ns.db.position={point=point,relativePoint=relativePoint,x=x,y=y}
    end)
    f:SetBackdrop({bgFile="Interface\\DialogFrame\\UI-DialogBox-Background",
        edgeFile="Interface\\Tooltips\\UI-Tooltip-Border",tile=true,tileSize=16,edgeSize=16,
        insets={left=4,right=4,top=4,bottom=4}})
    f:SetBackdropColor(0.05,0.06,0.08,0.97)
    local title=f:CreateFontString(nil,"OVERLAY","GameFontNormalLarge")
    title:SetPoint("TOPLEFT",18,-15); title:SetText("ProfessionGuide |cff999999Forever|r")
    button(f,"Close",60,580,-10,function() ns.db.hidden=true; f:Hide() end)
    ns.profButton=button(f,"Profession",225,18,-47,function()
        local list=ns.KnownProfessions()
        for i,slug in ipairs(list) do
            if slug==ns.db.selected then ns.db.selected=list[i%#list+1]; ns.Render(true); return end
        end
        ns.db.selected=list[1]; ns.Render(true)
    end)
    local label=f:CreateFontString(nil,"OVERLAY","GameFontNormal")
    label:SetPoint("TOPLEFT",260,-53); label:SetText("Target:")
    local input=CreateFrame("EditBox",nil,f,"InputBoxTemplate")
    ns.targetInput=input; input:SetSize(55,24); input:SetPoint("TOPLEFT",315,-47)
    input:SetAutoFocus(false); input:SetNumeric(true); input:SetMaxLetters(3)
    input:SetScript("OnEscapePressed",function(self) self:ClearFocus() end)
    local function apply()
        local ok,message=ns.SetTarget(input:GetText())
        ns.status=message; input:ClearFocus(); ns.Render()
    end
    input:SetScript("OnEnterPressed",apply)
    button(f,"Apply target",115,385,-47,apply)
    button(f,"Clear target",120,515,-47,function()
        if ns.db.selected then ns.db.targets[ns.db.selected]=nil end
        ns.status="Target cleared. Existing farming goals are unchanged."; ns.Render(true)
    end)
    local scroll=CreateFrame("ScrollFrame",nil,f,"UIPanelScrollFrameTemplate")
    ns.scroll=scroll; scroll:SetPoint("TOPLEFT",18,-88); scroll:SetSize(594,445)
    local child=CreateFrame("Frame",nil,scroll); child:SetSize(588,445); scroll:SetScrollChild(child)
    local text=child:CreateFontString(nil,"OVERLAY","GameFontHighlight")
    ns.body=text; ns.bodyFrame=child
    text:SetPoint("TOPLEFT"); text:SetWidth(580); text:SetJustifyH("LEFT"); text:SetJustifyV("TOP")
    ns.exportButton=button(f,"Export materials to ItemFarmingTool",305,18,-548,function()
        -- Re-read the live character before an explicit export click.
        ns.Refresh()
        local _,message=ns.Export(ns.plan); ns.status=message; ns.Render()
    end)
    button(f,"Refresh",90,335,-548,function() ns.Refresh() end)
    local status=f:CreateFontString(nil,"OVERLAY","GameFontHighlightSmall")
    ns.statusText=status; status:SetPoint("TOPLEFT",18,-582); status:SetWidth(620); status:SetJustifyH("LEFT")
    if UISpecialFrames then UISpecialFrames[#UISpecialFrames+1]="ProfessionGuideFrame" end
    f:SetScript("OnHide",function() if ns.db then ns.db.hidden=true end end)
    ns.ApplyPosition()
end
function ns.ApplyPosition()
    local p=ns.db.position
    ns.frame:ClearAllPoints()
    if p then ns.frame:SetPoint(p.point,UIParent,p.relativePoint,p.x,p.y)
    else ns.frame:SetPoint("CENTER") end
end
function ns.Render(resetInput)
    if not ns.frame or not ns.player then return end
    local slug=ns.db.selected
    local skill=slug and ns.player.professions[slug]
    local lines={"Character level "..ns.player.level.."  |  "..(ns.player.faction or "Unknown faction"),""}
    ns.profButton:SetText(skill and (skill.name.."  "..skill.rank.."/"..skill.cap.."  >") or "No profession detected")
    local target=slug and ns.db.targets[slug]
    if resetInput or not ns.targetInput:HasFocus() then ns.targetInput:SetText(target and tostring(target) or "") end
    ns.plan=nil
    if skill then
        local guide=ns.Guides[slug]
        lines[#lines+1]="|cffffd166"..skill.name.." - next steps|r"
        if ns.TrainerHints[slug] then
            lines[#lines+1]=ns.TrainerHints[slug]
            lines[#lines+1]="Trainer pairs above: Alliance / Horde."
        end
        if target then
            ns.plan=ns.Plan(slug,ns.player,target)
        else
            lines[#lines+1]="Choose a target and press Apply target to calculate a material list."
            -- Guide preview only. No shopping plan or integration writes.
            for _,s in ipairs(guide.steps) do
                if s.to>skill.rank then
                    lines[#lines+1]="Next skill band: "..math.max(skill.rank,s.from).."-"..s.to
                    for _,r in ipairs(s.recipes or {}) do lines[#lines+1]="Craft "..r.name.."." end
                    if s.action then lines[#lines+1]=s.action end
                    break
                end
            end
        end
        local p=ns.plan
        if p then
            lines[#lines+1]="Target: "..p.target
            if p.complete then lines[#lines+1]="Target reached." end
            for _,warning in ipairs(p.warnings) do lines[#lines+1]="|cffffbf69"..warning.."|r" end
            lines[#lines+1]=""
            for _,s in ipairs(p.steps) do
                lines[#lines+1]="|cffffd166"..s.from.."-"..s.to.."|r"
                for _,r in ipairs(s.recipes) do lines[#lines+1]="  About "..r.crafts.." crafts: "..r.name end
                if s.action then lines[#lines+1]=s.action end
            end
            lines[#lines+1]=""
            lines[#lines+1]="|cffffd166Materials for the remaining route|r"
            if #p.materials==0 then lines[#lines+1]="No consumable material list for this route." end
            for _,m in ipairs(p.materials) do
                lines[#lines+1]=m.quantity.." x "..m.name.."  (bags "..m.owned..", short "..math.max(0,m.quantity-m.owned)..")"
            end
            lines[#lines+1]="Estimates: partial bands are scaled; yellow/green recipes may need extra crafts."
            lines[#lines+1]="Retain crafted intermediate supplies for later steps. Missing intermediates are expanded into ingredients; owned intermediates reduce those needs."
            lines[#lines+1]="Train each recipe before crafting. Tools, books and recipe purchases are separate. Imperial Plate recipe bars and the Artisan Cooking quest supplies are included when needed."
        end
        lines[#lines+1]=""
        lines[#lines+1]="Source: WoW-Professions.com (snapshot 2026-11-12)"
        lines[#lines+1]=guide.source
        lines[#lines+1]="Default route only; no live auction prices or automatic crafting."
    else
        lines[#lines+1]="Learn a profession, then click Refresh. All primary and secondary professions are supported."
    end
    if ns.player.collapsed then lines[#lines+1]="Some skill categories are collapsed. Expand them in Skills if a profession is missing." end
    local body=table.concat(lines,"\n")
    ns.body:SetText(body)
    local height=ns.body:GetStringHeight()+20
    ns.bodyFrame:SetHeight(math.max(445,height))
    if resetInput then ns.scroll:SetVerticalScroll(0) end
    ns.exportButton:SetEnabled(ns.CanExport() and ns.plan~=nil and #ns.plan.materials>0)
    ns.statusText:SetText(ns.status or (ns.CanExport() and "Exports happen only when you click Export. Existing higher goals are preserved." or "ItemFarmingTool not loaded. Guide and material preview remain available."))
    if ns.db.hidden then ns.frame:Hide() else ns.frame:Show() end
end
