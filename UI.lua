-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
local GOLD, MUTED, GREEN = "|cffdbbc75", "|cffb5b1a8", "|cff94c49e"
local BOOK = "Interface\\Icons\\INV_Misc_Book_09"
local BAG = "Interface\\Icons\\INV_Misc_Bag_10"
local function actionIcon(name,label) return ns.IconTag("Interface\\Icons\\"..name)..label end
local function text(parent, font, width, align)
    local label=parent:CreateFontString(nil,"OVERLAY",font or "GameFontHighlight")
    label:SetWidth(width); label:SetJustifyH(align or "LEFT"); label:SetJustifyV("TOP")
    return label
end
local function place(label,value,x,y)
    label:ClearAllPoints(); label:SetPoint("TOPLEFT",x,-y); label:SetText(value)
    return y+label:GetStringHeight()
end
local function button(parent,label,w,x,y,callback)
    local b=CreateFrame("Button",nil,parent,"BackdropTemplate")
    b:SetSize(w,26); b:SetPoint("TOPLEFT",x,-y)
    b:SetBackdrop({bgFile="Interface\\Buttons\\WHITE8X8",edgeFile="Interface\\Tooltips\\UI-Tooltip-Border",edgeSize=8,
        insets={left=2,right=2,top=2,bottom=2}})
    b:SetBackdropColor(0.18,0.17,0.13,1); b:SetBackdropBorderColor(0.48,0.40,0.25,1)
    local caption=text(b,"GameFontHighlight",w-14,"CENTER")
    caption:SetPoint("CENTER"); caption:SetTextColor(0.86,0.74,0.46)
    b:SetFontString(caption); b:SetText(label); b:SetScript("OnClick",callback)
    b:SetScript("OnEnter",function(self) if self:IsEnabled() then self:SetBackdropColor(0.28,0.25,0.17,1) end end)
    b:SetScript("OnLeave",function(self) self:SetBackdropColor(0.18,0.17,0.13,1) end)
    b:SetScript("OnDisable",function() caption:SetTextColor(0.48,0.47,0.43) end)
    b:SetScript("OnEnable",function() caption:SetTextColor(0.86,0.74,0.46) end)
    return b
end
local function line(parent,x,y,w)
    local t=parent:CreateTexture(nil,"BORDER")
    t:SetColorTexture(0.35,0.33,0.28,0.6); t:SetSize(w,1); t:SetPoint("TOPLEFT",x,-y)
end
local function scroll(parent,x,y,w,h)
    local f=CreateFrame("ScrollFrame",nil,parent,"UIPanelScrollFrameTemplate")
    f:SetPoint("TOPLEFT",x,-y); f:SetSize(w,h)
    local child=CreateFrame("Frame",nil,f); child:SetSize(w,h); f:SetScrollChild(child)
    return f,child
end
local function panel(parent,x,y,w,h)
    local f=CreateFrame("Frame",nil,parent,"BackdropTemplate")
    f:SetSize(w,h); f:SetPoint("TOPLEFT",x,-y)
    f:SetBackdrop({bgFile="Interface\\Buttons\\WHITE8X8"})
    f:SetBackdropColor(0.10,0.12,0.15,1)
    return f
end

function ns.CreateUI()
    if ns.frame then return end
    local f=CreateFrame("Frame","ProfessionGuideFrame",UIParent,"BackdropTemplate")
    ns.frame=f; f:SetSize(860,680); f:SetPoint("CENTER"); f:SetClampedToScreen(true)
    f:SetMovable(true); f:EnableMouse(true); f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart",function(self) self:StartMoving() end)
    f:SetScript("OnDragStop",function(self)
        self:StopMovingOrSizing()
        local point,_,relativePoint,x,y=self:GetPoint()
        ns.db.position={point=point,relativePoint=relativePoint,x=x,y=y}
    end)
    f:SetBackdrop({bgFile="Interface\\Buttons\\WHITE8X8",
        edgeFile="Interface\\Tooltips\\UI-Tooltip-Border",edgeSize=12,
        insets={left=3,right=3,top=3,bottom=3}})
    f:SetBackdropColor(0.065,0.078,0.095,1)
    f:SetBackdropBorderColor(0.40,0.36,0.27,1)
    local emblem=f:CreateTexture(nil,"ARTWORK"); emblem:SetSize(24,24); emblem:SetPoint("TOPLEFT",20,-15)
    emblem:SetTexture(BOOK)
    place(text(f,"GameFontNormalLarge",350),GOLD.."ProfessionGuide|r",52,18)
    ns.characterText=text(f,"GameFontHighlightSmall",260,"RIGHT")
    ns.characterText:SetPoint("TOPRIGHT",-100,-23)
    button(f,"Close",64,778,14,function() ns.db.hidden=true; f:Hide() end)
    line(f,18,53,824)
    ns.profButton=button(f,"Profession",274,20,68,function()
        local list=ns.KnownProfessions()
        for i,slug in ipairs(list) do
            if slug==ns.db.selected then ns.db.selected=list[i%#list+1]; ns.status=nil; ns.Render(true); return end
        end
        ns.db.selected=list[1]; ns.Render(true)
    end)
    place(text(f,"GameFontNormal",80),"Target skill",326,75)
    local input=CreateFrame("EditBox",nil,f,"InputBoxTemplate")
    ns.targetInput=input; input:SetSize(55,26); input:SetPoint("TOPLEFT",412,-68)
    input:SetAutoFocus(false); input:SetNumeric(true); input:SetMaxLetters(3)
    input:SetScript("OnEscapePressed",function(self) self:ClearFocus() end)
    local function apply()
        local _,message=ns.SetTarget(input:GetText())
        ns.status=message; input:ClearFocus(); ns.Render(true)
    end
    input:SetScript("OnEnterPressed",apply)
    ns.applyButton=button(f,actionIcon("INV_Misc_Map_01","Plan route"),118,486,68,apply)
    ns.clearButton=button(f,actionIcon("INV_Misc_Note_01","Clear target"),112,614,68,function()
        if ns.db.selected then ns.db.targets[ns.db.selected]=nil end
        ns.status="Target cleared. Existing farming goals are unchanged."; ns.Render(true)
    end)
    button(f,actionIcon("INV_Misc_PocketWatch_01","Refresh"),104,738,68,function() ns.Refresh() end)
    local left=panel(f,16,112,216,496)
    place(text(left,"GameFontNormalSmall",180),MUTED.."LEVELING ROUTE|r",12,12)
    ns.routeScroll,ns.routeChild=scroll(left,10,39,174,440)
    ns.routeButtons={}; ns.materialRows={}
    ns.scroll,ns.bodyFrame=scroll(f,254,120,570,480)
    ns.stepHeading=text(ns.bodyFrame,"GameFontNormal",546)
    ns.recipeText=text(ns.bodyFrame,"GameFontNormalLarge",484)
    ns.recipeIcon=ns.bodyFrame:CreateTexture(nil,"ARTWORK"); ns.recipeIcon:SetSize(42,42)
    ns.detailText=text(ns.bodyFrame,"GameFontHighlight",546)
    ns.warningText=text(ns.bodyFrame,"GameFontHighlightSmall",546)
    ns.shoppingTitle=text(ns.bodyFrame,"GameFontNormalLarge",546)
    ns.materialMessage=text(ns.bodyFrame,"GameFontHighlight",546)
    ns.tableHead={}
    for i,col in ipairs({{0,290,"Material"},{302,66,"Have"},{382,66,"Need"},{464,66,"Short"}}) do
        ns.tableHead[i]={label=text(ns.bodyFrame,"GameFontHighlightSmall",col[2],i==1 and "LEFT" or "RIGHT"),x=col[1],title=col[3]}
    end
    ns.notesText=text(ns.bodyFrame,"GameFontHighlight",546)
    line(f,18,618,824)
    ns.notesButton=button(f,"Training & notes",162,20,631,function()
        ns.showNotes=not ns.showNotes; ns.Render(); ns.scroll:SetVerticalScroll(0)
    end)
    place(text(f,"GameFontHighlightSmall",265),MUTED.."WoW-Professions.com  /  Forever|r",206,640)
    ns.exportButton=button(f,actionIcon("INV_Misc_Bag_10","Export to ItemFarmingTool"),254,588,631,function()
        ns.Refresh()
        local _,message=ns.Export(ns.plan); ns.status=message; ns.Render()
    end)
    ns.statusText=text(f,"GameFontHighlightSmall",820)
    ns.statusText:SetPoint("TOPLEFT",20,-664)
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

-- Keep the chosen skill band through bag updates; advance after its completion.
function ns.BuildRoute(slug,skill)
    local rows={}
    if ns.plan then
        for _,step in ipairs(ns.plan.steps) do rows[#rows+1]=step end
    elseif skill then
        for _,step in ipairs(ns.Guides[slug].steps) do
            if step.to>skill.rank then rows[#rows+1]=step end
        end
    end
    local selected=1
    for i,step in ipairs(rows) do
        if ns.routeSelection and ns.routeSelection.slug==slug and ns.routeSelection.to==step.to then selected=i; break end
    end
    ns.route=rows; ns.selectedStep=rows[selected]
    ns.routeSelection=ns.selectedStep and {slug=slug,to=ns.selectedStep.to} or nil
    local y=0
    for i,step in ipairs(rows) do
        local b=ns.routeButtons[i]
        if not b then
            b=CreateFrame("Button",nil,ns.routeChild,"BackdropTemplate")
            b:SetWidth(174); b:SetBackdrop({bgFile="Interface\\Buttons\\WHITE8X8"})
            b.icon=b:CreateTexture(nil,"ARTWORK"); b.icon:SetSize(20,20); b.icon:SetPoint("TOPLEFT",8,-10)
            b.label=text(b,"GameFontHighlight",132); b.label:SetPoint("TOPLEFT",34,-9)
            b:SetScript("OnClick",function(self)
                ns.routeSelection={slug=ns.db.selected,to=self.step.to}
                ns.showNotes=false; ns.Render(); ns.scroll:SetVerticalScroll(0)
            end)
            ns.routeButtons[i]=b
        end
        b.step=step
        b.icon:SetTexture(ns.StepIcon(slug,step))
        local names={}
        for _,r in ipairs(step.recipes or {}) do names[#names+1]=r.name end
        local name=#names>0 and table.concat(names," / ") or "Gathering route"
        local range=math.max(skill.rank,step.from).."-"..step.to..(i==1 and "  |  Current" or "")
        b.label:SetText((i==selected and GOLD or MUTED)..range.."|r\n"..name)
        local height=math.max(52,b.label:GetStringHeight()+18)
        b:ClearAllPoints(); b:SetPoint("TOPLEFT",0,-y); b:SetHeight(height)
        b:SetBackdropColor(i==selected and 0.22 or 0.10,i==selected and 0.20 or 0.12,i==selected and 0.14 or 0.15,1)
        b:Show(); y=y+height+5
    end
    for i=#rows+1,#ns.routeButtons do ns.routeButtons[i]:Hide() end
    ns.routeChild:SetHeight(math.max(440,y))
end

local function sourceStep(slug,step)
    for _,s in ipairs(ns.Guides[slug].steps) do
        if s.from<=step.from and s.to>=step.to then return s end
    end
end

function ns.RenderRecipe(slug,skill)
    local step=ns.selectedStep
    local label=step and (math.max(skill.rank,step.from).."-"..step.to) or "Route complete"
    local y=place(ns.stepHeading,GOLD..label..(ns.route[1]==step and step and "  |  Current step" or "").."|r",0,0)+14
    ns.recipeIcon:ClearAllPoints(); ns.recipeIcon:SetPoint("TOPLEFT",0,-y)
    local recipes=step and step.recipes or {}
    local title,details={},{}
    local icon=ns.ProfessionIcon(slug)
    if step then
        local original=sourceStep(slug,step)
        for i,r in ipairs(recipes) do
            local recipe=original and original.recipes and original.recipes[i]
            local recipeIcon=recipe and ns.SpellIcon(recipe.spell)
            title[#title+1]=(i>1 and recipeIcon and ns.IconTag(recipeIcon,20) or "")..r.name
            if ns.plan then details[#details+1]="About "..r.crafts.." crafts" end
            if recipe then
                local ingredients={}
                for _,m in ipairs(recipe.materials) do
                    local materialIcon=ns.ItemIcon(ns.ItemIDs[m.name])
                    ingredients[#ingredients+1]=(materialIcon and ns.IconTag(materialIcon) or "")..m.quantity.." "..m.name
                end
                details[#details+1]=MUTED.."Per craft: "..table.concat(ingredients,", ").."|r"
                if i==1 then icon=recipeIcon or icon end
            end
        end
        if #recipes==0 then title[1]="Gathering route" end
        if step.action then details[#details+1]=step.action end
    else
        title[1]=ns.plan and ns.plan.complete and "Target reached" or "No further source steps"
        details[1]="Choose another target or view Training & notes."
    end
    ns.recipeIcon:SetTexture(icon); ns.recipeIcon:Show()
    y=math.max(y+46,place(ns.recipeText,table.concat(title,"\n"),56,y))+12
    y=place(ns.detailText,table.concat(details,"\n"),0,y)+18
    local warnings={}
    if ns.plan then for _,w in ipairs(ns.plan.warnings) do warnings[#warnings+1]=w end end
    if ns.player.collapsed then warnings[#warnings+1]="Expand collapsed Skills categories if a profession is missing." end
    ns.warningText:SetText("")
    if #warnings>0 then y=place(ns.warningText,"|cffffbf69"..table.concat(warnings,"\n").."|r",0,y)+18 end
    return y
end

function ns.RenderMaterials(y)
    y=place(ns.shoppingTitle,"Shopping list"..(ns.plan and "  "..MUTED.."to "..ns.plan.target.."|r" or ""),0,y)+12
    local materials=ns.plan and ns.plan.materials or {}
    for _,col in ipairs(ns.tableHead) do
        if #materials>0 then place(col.label,MUTED..col.title.."|r",col.x,y); col.label:Show()
        else col.label:Hide() end
    end
    if #materials>0 then y=y+24 end
    for i,m in ipairs(materials) do
        local row=ns.materialRows[i]
        if not row then
            row=CreateFrame("Frame",nil,ns.bodyFrame); row:SetWidth(546)
            row.icon=row:CreateTexture(nil,"ARTWORK"); row.icon:SetSize(24,24); row.icon:SetPoint("TOPLEFT",0,-3)
            row.name=text(row,"GameFontHighlight",260); row.name:SetPoint("TOPLEFT",34,-6)
            row.have=text(row,"GameFontHighlight",66,"RIGHT"); row.have:SetPoint("TOPLEFT",302,-6)
            row.need=text(row,"GameFontHighlight",66,"RIGHT"); row.need:SetPoint("TOPLEFT",382,-6)
            row.short=text(row,"GameFontHighlight",66,"RIGHT"); row.short:SetPoint("TOPLEFT",464,-6)
            row:EnableMouse(true)
            row:SetScript("OnEnter",function(self)
                if GameTooltip then GameTooltip:SetOwner(self,"ANCHOR_RIGHT"); GameTooltip:SetHyperlink("item:"..self.itemID); GameTooltip:Show() end
            end)
            row:SetScript("OnLeave",function() if GameTooltip then GameTooltip:Hide() end end)
            ns.materialRows[i]=row
        end
        row.itemID=m.id
        row.icon:SetTexture(ns.ItemIcon(m.id) or BAG); row.name:SetText(m.name)
        row.have:SetText(tostring(m.owned)); row.need:SetText(tostring(m.quantity))
        local short=math.max(0,m.quantity-m.owned)
        row.short:SetText((short==0 and GREEN or GOLD)..short.."|r")
        local height=math.max(32,row.name:GetStringHeight()+12)
        row:ClearAllPoints(); row:SetPoint("TOPLEFT",0,-y); row:SetHeight(height); row:Show(); y=y+height
    end
    for i=#materials+1,#ns.materialRows do ns.materialRows[i]:Hide() end
    local message=not ns.plan and "Choose a target and click Plan route to calculate supplies."
        or (#materials==0 and "No consumable materials for this route." or "Have = carried supplies. Need = entire remaining route.\nEstimated quantities; yellow/green recipes may need extra crafts.")
    y=place(ns.materialMessage,MUTED..message.."|r",0,y+12)+14
    return y
end

function ns.Render(resetInput)
    if not ns.frame or not ns.player then return end
    local slug=ns.db.selected
    local skill=slug and ns.player.professions[slug]
    local target=slug and ns.db.targets[slug]
    local context=(slug or "")..":"..tostring(target)
    if ns.routeContext~=context then
        ns.routeSelection=nil; ns.showNotes=false; ns.routeContext=context; resetInput=true
    end
    ns.characterText:SetText("Level "..ns.player.level.."  |  "..(ns.player.faction or "Unknown faction"))
    ns.profButton:SetText(skill and (ns.IconTag(ns.ProfessionIcon(slug),18)..skill.name.."  "..skill.rank.." / "..skill.cap.."   >") or "No profession detected")
    if resetInput or not ns.targetInput:HasFocus() then ns.targetInput:SetText(target and tostring(target) or "") end
    ns.plan=skill and target and ns.Plan(slug,ns.player,target) or nil
    ns.BuildRoute(slug,skill)
    local content={ns.stepHeading,ns.recipeText,ns.recipeIcon,ns.detailText,ns.warningText,ns.shoppingTitle,ns.materialMessage}
    for _,v in ipairs(content) do v:Hide() end
    for _,v in ipairs(ns.tableHead) do v.label:Hide() end
    for _,v in ipairs(ns.materialRows) do v:Hide() end
    ns.notesText:Hide()
    local height=480
    if skill and not ns.showNotes then
        for _,v in ipairs(content) do v:Show() end
        height=ns.RenderMaterials(ns.RenderRecipe(slug,skill))
    else
        local notes={}
        if skill then
            notes={GOLD.."Training & notes|r","",ns.TrainerHints[slug] or "Train profession ranks with your trainer as your skill increases.",
                "Trainer pairs: Alliance / Horde.",""}
            for _,r in ipairs(ns.RankRequirements(slug)) do
                notes[#notes+1]=r.name..": skill "..r.skill..", character level "..r.level.." (to pass "..r.cap..")."
            end
            notes[#notes+1]="\nKeep crafted intermediate supplies for later steps. Missing intermediates are expanded into ingredients; carried intermediates reduce those needs."
            notes[#notes+1]="\nTools, books, recipe purchases and training fees are separate. Imperial Plate recipe bars and Artisan Cooking quest supplies are included when needed."
            notes[#notes+1]="\nExport adds minimum total goals. Higher existing goals are preserved. Old goals are not removed; shared items across separate plans are not added together."
            notes[#notes+1]="\nSource: WoW-Professions.com (2026-11-12)\n"..ns.Guides[slug].source
            notes[#notes+1]="\nDefault routes only. Higher-level routes are provisional; Tailoring ends at 265. No live auction prices or automatic crafting."
            if slug=="lockpicking" then notes[#notes+1]="\nLockpicking cap: five times your character level, up to 300." end
        else
            notes={GOLD.."No profession detected|r","","Learn a profession, then click Refresh. Expand collapsed categories in the Skills panel if a profession is missing."}
        end
        ns.notesText:Show(); height=place(ns.notesText,table.concat(notes,"\n"),0,0)+20
    end
    ns.bodyFrame:SetHeight(math.max(480,height))
    if resetInput then ns.scroll:SetVerticalScroll(0); ns.routeScroll:SetVerticalScroll(0) end
    ns.notesButton:SetText(actionIcon("INV_Misc_Book_09",ns.showNotes and "Back to workshop" or "Training & notes"))
    ns.exportButton:SetEnabled(ns.CanExport() and ns.plan~=nil and #ns.plan.materials>0)
    ns.statusText:SetText(ns.status or (ns.CanExport() and "ItemFarmingTool connected. Export only when you click; existing higher goals are preserved." or "ItemFarmingTool not loaded. Guide and shopping list remain available."))
    if ns.db.hidden then ns.frame:Hide() else ns.frame:Show() end
end
