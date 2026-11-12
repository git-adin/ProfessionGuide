-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
local function finite(n) return type(n)=="number" and n==n and math.abs(n)<math.huge end
function ns.PositionMinimapButton()
    local b=ns.minimapButton
    if not b or not Minimap then return end
    local angle=math.rad(ns.db.minimapAngle)
    local x,y=math.cos(angle),math.sin(angle)
    if GetMinimapShape and GetMinimapShape()=="SQUARE" then
        local edge=math.max(math.abs(x),math.abs(y)); x,y=x/edge,y/edge
    end
    b:ClearAllPoints()
    b:SetPoint("CENTER",Minimap,"CENTER",x*(Minimap:GetWidth()/2+8),y*(Minimap:GetHeight()/2+8))
end
function ns.UpdateMinimapButton()
    if not ns.minimapButton then return end
    ns.PositionMinimapButton()
    ns.minimapButton:SetShown(ns.db.minimapButton)
end
function ns.InitMinimapButton()
    if ns.minimapButton or not Minimap then return end
    local b=CreateFrame("Button","ProfessionGuideMinimapButton",Minimap)
    ns.minimapButton=b
    b:SetSize(31,31); b:SetFrameLevel(Minimap:GetFrameLevel()+8)
    b:RegisterForClicks("LeftButtonUp"); b:RegisterForDrag("LeftButton")
    local background=b:CreateTexture(nil,"BACKGROUND")
    background:SetTexture("Interface\\Minimap\\UI-Minimap-Background")
    background:SetSize(24,24); background:SetPoint("CENTER")
    local icon=b:CreateTexture(nil,"ARTWORK")
    icon:SetTexture("Interface\\Icons\\INV_Misc_Book_09")
    icon:SetSize(20,20); icon:SetPoint("CENTER"); icon:SetTexCoord(0.08,0.92,0.08,0.92)
    local border=b:CreateTexture(nil,"OVERLAY")
    border:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")
    border:SetSize(54,54); border:SetPoint("TOPLEFT")
    b:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
    b:SetScript("OnClick",function() ns.Toggle() end)
    b:SetScript("OnEnter",function(self)
        if not GameTooltip then return end
        GameTooltip:SetOwner(self,"ANCHOR_LEFT")
        GameTooltip:AddLine("ProfessionGuide",1,0.82,0)
        GameTooltip:AddLine("Click to open or close the Workshop.",1,1,1)
        GameTooltip:AddLine("Drag to move around the minimap.",0.7,0.7,0.7)
        GameTooltip:Show()
    end)
    b:SetScript("OnLeave",function() if GameTooltip then GameTooltip:Hide() end end)
    b:SetScript("OnDragStart",function(self)
        if GameTooltip then GameTooltip:Hide() end
        self:SetScript("OnUpdate",function()
            local scale=Minimap:GetEffectiveScale()
            local mx,my=Minimap:GetCenter()
            local px,py=GetCursorPosition()
            if not finite(scale) or scale<=0 or not finite(mx) or not finite(my) or not finite(px) or not finite(py) then return end
            local dx,dy=px/scale-mx,py/scale-my
            if dx==0 and dy==0 then return end
            ns.db.minimapAngle=math.deg(math.atan2(dy,dx))%360
            ns.PositionMinimapButton()
        end)
    end)
    local function stop(self) self:SetScript("OnUpdate",nil) end
    b:SetScript("OnDragStop",stop)
    b:SetScript("OnHide",function(self) stop(self); if GameTooltip then GameTooltip:Hide() end end)
    Minimap:HookScript("OnSizeChanged",ns.PositionMinimapButton)
    ns.UpdateMinimapButton()
end
