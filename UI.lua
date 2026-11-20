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
    b.caption=caption
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
    -- Keep the window's children together when overlapping other addon windows.
    f:SetFrameStrata("MEDIUM"); f:SetToplevel(true)
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
        local ok,message=ns.SetTarget(input:GetText())
        ns.status=message; input:ClearFocus(); ns.Render(true)
        if ok then
            local favorites=ns.FavoritePlanRecipes(ns.plan)
            if favorites~="" then ns.status=message.." "..favorites; ns.statusText:SetText(ns.status) end
        end
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
    ns.routeButtons={}; ns.materialRows={}; ns.costCards={}
    ns.scroll,ns.bodyFrame=scroll(f,254,120,570,480)
    ns.stepHeading=text(ns.bodyFrame,"GameFontNormal",546)
    ns.recipeText=text(ns.bodyFrame,"GameFontNormalLarge",484)
    ns.recipeIcon=ns.bodyFrame:CreateTexture(nil,"ARTWORK"); ns.recipeIcon:SetSize(42,42)
    ns.detailText=text(ns.bodyFrame,"GameFontHighlight",546)
    ns.warningText=text(ns.bodyFrame,"GameFontHighlightSmall",546)
    ns.shoppingTitle=text(ns.bodyFrame,"GameFontNormalLarge",546)
    ns.materialMessage=text(ns.bodyFrame,"GameFontHighlightSmall",546)
    ns.preparedText=text(ns.bodyFrame,"GameFontHighlightSmall",546)
    ns.tableHead={}
    for i,col in ipairs({{0,290,"Material"},{302,66,"In bags"},{382,66,"Required"},{464,66,"To get"}}) do
        ns.tableHead[i]={label=text(ns.bodyFrame,"GameFontHighlightSmall",col[2],i==1 and "LEFT" or "RIGHT"),x=col[1],title=col[3]}
    end
    ns.notesText=text(ns.bodyFrame,"GameFontHighlight",546)
    ns.optionButton=button(ns.bodyFrame,"Recipe option",546,0,0,function() ns.OpenAlternateMenu() end)
    ns.compareButton=button(ns.bodyFrame,"Compare alternatives",176,0,0,function()
        ns.showComparison=not ns.showComparison; ns.Render()
    end)
    ns.compareText=text(ns.bodyFrame,"GameFontHighlightSmall",546)
    ns.choiceDeltaText=text(ns.bodyFrame,"GameFontHighlightSmall",546)
    ns.exportReviewText=text(ns.bodyFrame,"GameFontHighlightSmall",546)
    ns.alternateMenu=CreateFrame("Frame",nil,f,"BackdropTemplate")
    ns.alternateMenu:SetWidth(546); ns.alternateMenu:SetClampedToScreen(true)
    ns.alternateMenu:SetFrameLevel(f:GetFrameLevel()+20)
    ns.alternateMenu:SetBackdrop({bgFile="Interface\\Buttons\\WHITE8X8",edgeFile="Interface\\Tooltips\\UI-Tooltip-Border",edgeSize=12})
    ns.alternateMenu:SetBackdropColor(0.10,0.12,0.15,1)
    ns.alternateMenu:SetBackdropBorderColor(0.48,0.40,0.25,1)
    ns.alternateMenu.buttons={}; ns.alternateMenu:Hide()
    ns.scroll:HookScript("OnVerticalScroll",function() ns.alternateMenu:Hide() end)
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
    f:SetScript("OnHide",function() if ns.db then ns.db.hidden=true end; ns.alternateMenu:Hide() end)
    ns.ApplyPosition()
end

function ns.OpenAlternateMenu()
    local menu=ns.alternateMenu
    if menu:IsShown() then menu:Hide(); return end
    local slug=ns.db.selected
    local group=ns.GroupForStep(slug,ns.selectedStep)
    if not group then return end
    local active=ns.SelectedOption(slug,group)
    menu:ClearAllPoints(); menu:SetPoint("TOPLEFT",ns.optionButton,"BOTTOMLEFT",0,-2)
    local y=8
    for i,option in ipairs(group.options) do
        local b=menu.buttons[i]
        if not b then
            b=button(menu,"",526,10,y,function(self)
                local ok,message=ns.SetChoice(ns.db.selected,self.groupID,self.optionID)
                if not ok then ns.status=message end
                ns.Render()
            end)
            menu.buttons[i]=b
        end
        b.groupID,b.optionID=group.id,option.id
        local label=(active.id==option.id and "> " or "")..option.label
        if option.faction then label=label.." ("..option.faction.." only)" end
        b:SetText(label)
        b:SetEnabled(not option.faction or ns.player.faction==option.faction)
        local height=math.max(30,b.caption:GetStringHeight()+10)
        b:ClearAllPoints(); b:SetPoint("TOPLEFT",10,-y); b:SetHeight(height); b:Show()
        y=y+height+4
    end
    for i=#group.options+1,#menu.buttons do menu.buttons[i]:Hide() end
    menu:SetHeight(y+4); menu:Show()
end

function ns.RenderChoices(slug,step,y)
    local group=ns.GroupForStep(slug,step)
    if not group then return y end
    local option=ns.SelectedOption(slug,group)
    ns.optionButton:SetText("Recipe option: "..option.label.."  v")
    local height=math.max(28,ns.optionButton.caption:GetStringHeight()+10)
    ns.optionButton:ClearAllPoints(); ns.optionButton:SetPoint("TOPLEFT",0,-y); ns.optionButton:SetHeight(height); ns.optionButton:Show()
    y=y+height+6
    ns.compareButton:ClearAllPoints(); ns.compareButton:SetPoint("TOPLEFT",0,-y)
    ns.compareButton:SetText(ns.showComparison and "Hide comparisons" or "Compare alternatives"); ns.compareButton:Show()
    y=y+36
    if ns.showComparison then
        local lines={}
        for _,candidate in ipairs(group.options) do
            lines[#lines+1]=GOLD..candidate.label.."|r"
            if candidate.note~="" then lines[#lines+1]=candidate.note end
            if candidate.level>1 then lines[#lines+1]="Character level "..candidate.level.." required." end
            if candidate.faction then lines[#lines+1]=candidate.faction.." only." end
            lines[#lines+1]=ns.CompareChoice(slug,group,candidate)
            lines[#lines+1]=""
        end
        ns.compareText:Show(); y=place(ns.compareText,table.concat(lines,"\n"),0,y)+12
    elseif option.note~="" and not ns.plan then
        ns.compareText:Show(); y=place(ns.compareText,MUTED..option.note.."|r",0,y)+12
    end
    return y
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
        for _,step in ipairs(ns.GetGuideSteps(slug)) do
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
    for _,s in ipairs(ns.GetGuideSteps(slug)) do
        if s.from<=step.from and s.to>=step.to then return s end
    end
end

function ns.RenderCostCard(recipe,crafts,index,y,multiple)
    local card=ns.costCards[index]
    if not card then
        card=panel(ns.bodyFrame,0,0,546,80)
        card.title=text(card,"GameFontNormal",292); card.title:SetPoint("TOPLEFT",12,-10)
        card.each=text(card,"GameFontHighlightSmall",108,"RIGHT"); card.each:SetPoint("TOPLEFT",308,-10); card.each:SetText("Each craft")
        card.total=text(card,"GameFontHighlightSmall",106,"RIGHT"); card.total:SetPoint("TOPLEFT",426,-10); card.total:SetText("This step")
        card.rows={}
        for i=1,2 do
            local row={label=text(card,"GameFontHighlightSmall",280),each=text(card,"GameFontHighlight",108,"RIGHT"),total=text(card,"GameFontHighlight",106,"RIGHT")}
            card.rows[i]=row
        end
        card.footer=text(card,"GameFontHighlightSmall",520)
        card:EnableMouse(true)
        card:SetScript("OnEnter",function(self)
            if not GameTooltip then return end
            GameTooltip:SetOwner(self,"ANCHOR_RIGHT")
            GameTooltip:ClearLines()
            GameTooltip:AddLine("Pricing details",1,0.82,0)
            for _,row in ipairs(self.helpRows) do
                GameTooltip:AddDoubleLine(row[1],row[2],0.7,0.7,0.7,1,1,1)
            end
            if #self.missingPrices>0 then
                GameTooltip:AddLine(" ")
                GameTooltip:AddLine("Missing ingredient prices",1,0.75,0.4)
                for _,name in ipairs(self.missingPrices) do GameTooltip:AddLine("• "..name,1,1,1,true) end
            end
            GameTooltip:AddLine(" ")
            GameTooltip:AddLine(self.helpNote,0.7,0.7,0.7,true)
            GameTooltip:Show()
        end)
        card:SetScript("OnLeave",function() if GameTooltip then GameTooltip:Hide() end end)
        ns.costCards[index]=card
    end
    local cost=ns.CraftCost(recipe)
    card.title:SetText(multiple and recipe.name or "Estimated material cost")
    local rowY=math.max(34,card.title:GetStringHeight()+18)
    card.each:SetShown(cost~=nil); card.total:SetShown(cost~=nil)
    for _,row in ipairs(card.rows) do row.label:Hide(); row.each:Hide(); row.total:Hide() end
    if cost then
        local quotes={}
        if cost.lowLabel then quotes[#quotes+1]={cost.lowLabel,cost.low,cost.missingLow} end
        if cost.averageLabel then quotes[#quotes+1]={cost.averageLabel,cost.average,cost.missingAverage} end
        for i,quote in ipairs(quotes) do
            local row=card.rows[i]
            local complete=#quote[3]==0
            place(row.label,MUTED..quote[1].."|r",12,rowY)
            place(row.each,complete and ns.FormatCost(quote[2]) or "|cffffbf69Missing prices|r",308,rowY)
            place(row.total,complete and crafts and (GOLD..ns.FormatCost(quote[2]*crafts).."|r") or MUTED.."—|r",426,rowY)
            row.label:Show(); row.each:Show(); row.total:Show()
            rowY=rowY+22
        end
        local stamp=type(cost.scannedAt)=="number" and cost.scannedAt>0 and cost.scannedAt<math.huge
            and ns.Safe(date,"%m/%d %H:%M",cost.scannedAt)
        local footer=cost.source..(stamp and ("  •  "..stamp) or "")
            ..(crafts and ("  •  ~"..crafts.." crafts") or "  •  Choose a target for step totals")
        card.footer:SetText(MUTED..footer.."  •  Details on hover|r")
    else
        rowY=30
        card.footer:SetText(MUTED.."No pricing data provider • Guide and planning remain available|r")
    end
    card.helpRows={{"Source",cost and cost.source or "Not available"},
        {"Scope",crafts and "Selected step" or "Per craft; no target"},
        {"Owned materials","Included in value"}}
    if (recipe.yield or 1)>1 then card.helpRows[#card.helpRows+1]={"Output",recipe.yield.." items per craft"} end
    card.missingPrices={}
    local seen={}
    if cost then
        for _,missing in ipairs({cost.lowLabel and cost.missingLow or {},cost.averageLabel and cost.missingAverage or {}}) do
            for _,name in ipairs(missing) do
                if not seen[name] then card.missingPrices[#card.missingPrices+1]=name; seen[name]=true end
            end
        end
    end
    card.helpNote=cost and "Saved prices; may have changed." or "Enable a supported pricing addon for estimates."
    card.footer:ClearAllPoints(); card.footer:SetPoint("TOPLEFT",12,-rowY)
    local height=rowY+card.footer:GetStringHeight()+10
    card:ClearAllPoints(); card:SetPoint("TOPLEFT",0,-y); card:SetHeight(height); card:Show()
    return y+height+14
end

function ns.RenderRecipe(slug,skill)
    local step=ns.selectedStep
    local label=step and (math.max(skill.rank,step.from).."-"..step.to) or "Route complete"
    local y=place(ns.stepHeading,GOLD..label..(ns.route[1]==step and step and "  |  Current step" or "").."|r",0,0)+14
    y=ns.RenderChoices(slug,step,y)
    ns.recipeIcon:ClearAllPoints(); ns.recipeIcon:SetPoint("TOPLEFT",0,-y)
    local recipes=step and step.recipes or {}
    local title,details,costs={},{},{}
    local icon=ns.ProfessionIcon(slug)
    if step then
        local original=sourceStep(slug,step)
        if original and original.note and not ns.plan then details[#details+1]=original.note end
        for i,r in ipairs(recipes) do
            local recipe=original and original.recipes and original.recipes[i]
            local recipeIcon=recipe and ns.RecipeIcon(recipe.spell)
            title[#title+1]=(i>1 and recipeIcon and ns.IconTag(recipeIcon,20) or "")..r.name
            if ns.plan then details[#details+1]=(r.minimum and "At least " or "About ")..r.crafts.." crafts"..(r.minimum and " (minimum only; allow extra materials)" or "") end
            if recipe then
                local ingredients={}
                for _,m in ipairs(recipe.materials) do
                    local materialIcon=ns.ItemIcon(ns.ItemIDs[m.name])
                    ingredients[#ingredients+1]=(materialIcon and ns.IconTag(materialIcon) or "")..m.quantity.." "..m.name
                end
                details[#details+1]=MUTED.."Per craft: "..table.concat(ingredients,", ").."|r"
                costs[#costs+1]={recipe=recipe,crafts=ns.plan and r.crafts or nil}
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
    y=place(ns.detailText,table.concat(details,"\n"),0,y)+12
    for i,cost in ipairs(costs) do y=ns.RenderCostCard(cost.recipe,cost.crafts,i,y,#costs>1) end
    local warnings={}
    if ns.plan then for _,w in ipairs(ns.plan.warnings) do warnings[#warnings+1]=w end end
    if ns.player.collapsed then warnings[#warnings+1]="Expand collapsed Skills categories if a profession is missing." end
    ns.warningText:SetText("")
    if #warnings>0 then y=place(ns.warningText,"|cffffbf69"..table.concat(warnings,"\n").."|r",0,y)+18 end
    if ns.choiceDelta then ns.choiceDeltaText:Show(); y=place(ns.choiceDeltaText,MUTED.."Last choice: "..ns.choiceDelta.."|r",0,y)+16 end
    local review=ns.ExportReview(ns.plan)
    if review then ns.exportReviewText:Show(); y=place(ns.exportReviewText,"|cffffbf69"..review.."|r",0,y)+16 end
    return y
end

function ns.RenderMaterials(y)
    if ns.plan and #ns.plan.prepared>0 then
        local lines={GOLD.."Prepared supplies|r"}
        for _,m in ipairs(ns.plan.prepared) do
            local icon=ns.ItemIcon(m.id)
            lines[#lines+1]=(icon and ns.IconTag(icon) or "")..m.name..": "..GREEN.."use "..m.used.." from bags|r; still need "..m.missing.."."
        end
        lines[#lines+1]=MUTED.."Only missing supplies are expanded into raw materials.|r"
        ns.preparedText:Show(); y=place(ns.preparedText,table.concat(lines,"\n"),0,y)+18
    end
    y=place(ns.shoppingTitle,"Shopping list"..(ns.plan and "  "..MUTED.."•  Target "..ns.plan.target.."|r" or "")..(ns.plan and ns.plan.minimum and " (minimum)" or ""),0,y)+12
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
            row.background=row:CreateTexture(nil,"BACKGROUND"); row.background:SetAllPoints()
            row.icon=row:CreateTexture(nil,"ARTWORK"); row.icon:SetSize(24,24); row.icon:SetPoint("TOPLEFT",6,-5)
            row.name=text(row,"GameFontHighlight",260); row.name:SetPoint("TOPLEFT",40,-9)
            row.have=text(row,"GameFontHighlight",66,"RIGHT"); row.have:SetPoint("TOPLEFT",302,-9)
            row.need=text(row,"GameFontHighlight",66,"RIGHT"); row.need:SetPoint("TOPLEFT",382,-9)
            row.short=text(row,"GameFontNormal",66,"RIGHT"); row.short:SetPoint("TOPLEFT",464,-9)
            row:EnableMouse(true)
            row:SetScript("OnEnter",function(self)
                if GameTooltip then GameTooltip:SetOwner(self,"ANCHOR_RIGHT"); GameTooltip:SetHyperlink("item:"..self.itemID); GameTooltip:Show() end
            end)
            row:SetScript("OnLeave",function() if GameTooltip then GameTooltip:Hide() end end)
            ns.materialRows[i]=row
        end
        row.itemID=m.id
        row.icon:SetTexture(ns.ItemIcon(m.id) or BAG); row.name:SetText(m.name)
        row.background:SetColorTexture(0.12,0.14,0.17,i%2==1 and 0.75 or 0.3)
        row.have:SetText(tostring(m.owned)); row.have:SetTextColor(0.71,0.69,0.66); row.need:SetText(tostring(m.quantity))
        local short=math.max(0,m.quantity-m.owned)
        row.short:SetText((short==0 and GREEN or GOLD)..short.."|r")
        local height=math.max(36,row.name:GetStringHeight()+18)
        row:ClearAllPoints(); row:SetPoint("TOPLEFT",0,-y); row:SetHeight(height); row:Show(); y=y+height
    end
    for i=#materials+1,#ns.materialRows do ns.materialRows[i]:Hide() end
    local message=not ns.plan and "Choose a target and click Plan route to calculate supplies."
        or (#materials==0 and "No consumable materials for this route." or "Entire remaining route • Bags only • Quantities are estimates")
    if ns.plan and ns.plan.minimum then message=message.."\nMinimum estimates only: source does not give a full craft count for this alternate." end
    y=place(ns.materialMessage,MUTED..message.."|r",0,y+12)+14
    return y
end

function ns.RenderTrainingNotes(slug,skill)
    local faction=ns.player.faction
    local factionLabel=(faction=="Horde" or faction=="Alliance") and faction or "Faction not detected"
    local heading={GOLD..ns.Professions[slug].name.." training|r",
        MUTED..factionLabel.."  |  Skill "..skill.rank.." / "..skill.cap.."  |  Level "..ns.player.level.."|r","",
        GOLD.."Rank requirements|r"}
    for _,rank in ipairs(ns.RankRequirements(slug)) do
        local state=skill.cap>rank.cap and "Trained" or
            (skill.rank>=rank.skill and ns.player.level>=rank.level and "Ready to train" or "Not ready")
        heading[#heading+1]=rank.name.." â€” skill "..rank.skill..", level "..rank.level.."  ("..state..")"
    end
    heading[#heading+1]=""
    heading[#heading+1]=GOLD.."Trainers & books|r"
    heading[#heading+1]=MUTED.."Click a blue name to replace your map waypoint. Neutral contacts are included.|r"
    if factionLabel=="Faction not detected" then heading[#heading+1]="Only neutral contacts shown until your faction is known." end
    ns.trainingHeader=ns.trainingHeader or text(ns.bodyFrame,"GameFontHighlight",546)
    ns.trainingHeader:Show()
    local y=place(ns.trainingHeader,table.concat(heading,"\n"),0,0)+12
    ns.trainingRows=ns.trainingRows or {}
    local trainers=ns.TrainersFor(slug)
    for i,entry in ipairs(trainers) do
        local row=ns.trainingRows[i]
        if not row then
            row=CreateFrame("Button",nil,ns.bodyFrame)
            row:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight")
            row.label=text(row,"GameFontHighlight",534); row.label:SetPoint("TOPLEFT",6,-4)
            row:SetScript("OnClick",function(self)
                local _,message=ns.PinTrainer(self.entry)
                ns.status=message; ns.statusText:SetText(message)
            end)
            ns.trainingRows[i]=row
        end
        row.entry=entry
        local pin=entry.map and entry.x and entry.y
        row:SetEnabled(not not pin)
        local name=pin and ("|cff66c7ff["..entry.name.."]|r") or entry.name
        local location=entry.location..(pin and ("  â€¢  "..entry.x..", "..entry.y) or "  â€¢  Pin not available")
        row.label:SetText(GOLD..entry.role.."|r  "..name.."\n"..MUTED..location.."|r"..(entry.note and ("\n"..entry.note) or ""))
        local height=row.label:GetStringHeight()+12
        row:ClearAllPoints(); row:SetPoint("TOPLEFT",0,-y); row:SetSize(546,height); row:Show()
        y=y+height+8
    end
    local notes={}
    if #trainers==0 then notes[#notes+1]="Visit a full profession trainer in a friendly capital. Ask a guard for directions." end
    local tips=ns.TrainingTips[slug]
    if tips then
        notes[#notes+1]=GOLD.."Profession notes|r"
        if tips.common then notes[#notes+1]=tips.common end
        if tips[faction] then notes[#notes+1]=tips[faction] end
        notes[#notes+1]=""
    end
    notes[#notes+1]=GOLD.."Planning supplies|r"
    notes[#notes+1]="Keep crafted intermediates. The shopping list credits carried supplies and expands only missing intermediates."
    notes[#notes+1]="Tools, books, patterns and training fees are separate."
    if slug=="blacksmithing" then notes[#notes+1]="Required Imperial Plate recipe quest bars are included in your plan." end
    if slug=="cooking" then notes[#notes+1]="Required Artisan Cooking quest supplies are included in your plan." end
    notes[#notes+1]=""
    notes[#notes+1]=GOLD.."Choices & exports|r"
    notes[#notes+1]="Compare alternatives before changing recipes. Linked steps change together; choices save per character."
    notes[#notes+1]="Export only updates farming goals when clicked. Higher goals stay; remove old goals manually. Separate plans do not add shared totals together."
    notes[#notes+1]=""
    notes[#notes+1]=GOLD.."Source & estimates|r"
    notes[#notes+1]="WoW-Professions.com / Forever â€” data checked "..ns.SourceDate
    notes[#notes+1]="Higher-level routes remain provisional; some alternates give minimum craft counts. Auction estimates use saved prices. Crafting is manual."
    ns.notesText:Show()
    return place(ns.notesText,table.concat(notes,"\n"),0,y+8)+20
end

function ns.Render(resetInput)
    if not ns.frame or not ns.player then return end
    local slug=ns.db.selected
    local skill=slug and ns.player.professions[slug]
    local target=slug and ns.db.targets[slug]
    local context=(slug or "")..":"..tostring(target)
    if ns.routeContext~=context then
        ns.routeSelection=nil; ns.showNotes=false; ns.showComparison=false; ns.choiceDelta=nil; ns.routeContext=context; resetInput=true
    end
    ns.characterText:SetText("Level "..ns.player.level.."  |  "..(ns.player.faction or "Unknown faction"))
    ns.profButton:SetText(skill and (ns.IconTag(ns.ProfessionIcon(slug),18)..skill.name.."  "..skill.rank.." / "..skill.cap.."   >") or "No profession detected")
    if resetInput or not ns.targetInput:HasFocus() then ns.targetInput:SetText(target and tostring(target) or "") end
    ns.plan=skill and target and ns.Plan(slug,ns.player,target) or nil
    ns.BuildRoute(slug,skill)
    ns.alternateMenu:Hide(); ns.optionButton:Hide(); ns.compareButton:Hide(); ns.compareText:Hide(); ns.choiceDeltaText:Hide(); ns.exportReviewText:Hide(); ns.preparedText:Hide()
    local content={ns.stepHeading,ns.recipeText,ns.recipeIcon,ns.detailText,ns.warningText,ns.shoppingTitle,ns.materialMessage}
    for _,v in ipairs(content) do v:Hide() end
    for _,v in ipairs(ns.tableHead) do v.label:Hide() end
    for _,v in ipairs(ns.materialRows) do v:Hide() end
    for _,card in ipairs(ns.costCards) do card:Hide() end
    ns.notesText:Hide()
    if ns.trainingHeader then ns.trainingHeader:Hide() end
    for _,row in ipairs(ns.trainingRows or {}) do row:Hide() end
    local height=480
    if skill and not ns.showNotes then
        for _,v in ipairs(content) do v:Show() end
        height=ns.RenderMaterials(ns.RenderRecipe(slug,skill))
    else
        if skill then height=ns.RenderTrainingNotes(slug,skill)
        else
            ns.notesText:Show()
            height=place(ns.notesText,GOLD.."No profession detected|r\n\nLearn a profession, then click Refresh. Expand collapsed Skills categories if needed.",0,0)+20
        end
    end
    ns.bodyFrame:SetHeight(math.max(480,height))
    if resetInput then ns.scroll:SetVerticalScroll(0); ns.routeScroll:SetVerticalScroll(0) end
    ns.notesButton:SetText(actionIcon("INV_Misc_Book_09",ns.showNotes and "Back to workshop" or "Training & notes"))
    local canExport, exportStatus = ns.CanExport()
    ns.exportButton:SetEnabled(canExport and ns.plan~=nil and #ns.plan.materials>0)
    ns.statusText:SetText(ns.status or (canExport and "ItemFarmingTool connected. Export only when you click. Existing higher goals are preserved." or exportStatus))
    if ns.db.hidden then ns.frame:Hide() else ns.frame:Show() end
end
