-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...

function ns.UpdateProfessionButton()
    local b=ns.professionButton
    if not b then return end
    local parent=ns.professionButtonParent
    b:ClearAllPoints()
    if parent.CloseButton then b:SetPoint("RIGHT",parent.CloseButton,"LEFT",-6,0)
    else b:SetPoint("TOPRIGHT",parent,"TOPRIGHT",-30,-1) end
    -- Portrait-frame borders and title controls sit above the recipe pages.
    local level=parent:GetFrameLevel()
    for _,key in ipairs({"BookPage","CraftingPage","NineSlice","TitleContainer","CloseButton"}) do
        if parent[key] then level=math.max(level,parent[key]:GetFrameLevel()) end
    end
    b:SetFrameLevel(level+1)
    b:Show()
end

function ns.InitProfessionButton()
    if ns.professionButton then ns.UpdateProfessionButton(); return end
    local parent=ProfessionsFrame or ProfessionsBookFrame
    if not parent then return end
    local b=CreateFrame("Button","ProfessionGuideProfessionsButton",parent,"UIPanelButtonTemplate")
    ns.professionButton=b
    ns.professionButtonParent=parent
    b:SetSize(88,20)
    parent:HookScript("OnShow",ns.UpdateProfessionButton)
    parent:HookScript("OnSizeChanged",ns.UpdateProfessionButton)
    for _,key in ipairs({"BookPage","CraftingPage"}) do
        if parent[key] then parent[key]:HookScript("OnShow",ns.UpdateProfessionButton) end
    end
    b:SetText(ns.IconTag("Interface\\Icons\\INV_Misc_Book_09").."Guide")
    b:SetScript("OnClick",function()
        if parent.CraftingPage and parent.CraftingPage:IsShown() then
            for slug,meta in pairs(ns.Professions) do
                if meta.id==parent.selectedSkillLine then ns.db.selected=slug; break end
            end
        end
        ns.Command("show")
        ns.frame:Raise()
    end)
    ns.UpdateProfessionButton()
end
