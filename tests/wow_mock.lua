-- Offline UI/inventory harness. No game client or services are used.
frames, timers, hooks, messages, bags, itemData = {}, {}, {}, {}, {}, {}
bankItems, equippedItems, reagentBankItems, accountBankItems = {}, {}, {}, {}
function time() return 1794240000 end
function date(_, stamp) return "11/09 12:00" end
NUM_BAG_SLOTS = 4
Enum = {BagIndex={ReagentBag=5}}
SlashCmdList = {}
local methods = {}
function methods:SetScript(key, value) self.scripts[key] = value end
function methods:GetScript(key) return self.scripts[key] end
function methods:RegisterEvent(key) self.events[key] = true end
function methods:UnregisterEvent(key) self.events[key] = nil end
function methods:SetSize(w, h) self.width, self.height = w, h end
function methods:SetHeight(h) self.height = h end
function methods:SetWidth(w) self.width = w end
function methods:GetWidth() return self.width end
function methods:GetHeight() return self.height end
function methods:SetPoint(...) self.point = {...} end
function methods:GetPoint() return unpack(self.point) end
function methods:ClearAllPoints() self.point = nil end
function methods:SetText(text) self.text = tostring(text) end
function methods:GetText() return self.text or "" end
function methods:Show() self.shown = true end
function methods:Hide()
    local was = self.shown
    self.shown = false
    if was and self.scripts.OnHide then self.scripts.OnHide(self) end
end
function methods:SetShown(value) if value then self:Show() else self:Hide() end end
function methods:IsShown() return self.shown and (not self.parent or self.parent:IsShown()) end
function methods:SetFocus() if focus then focus.focus = false end; focus = self; self.focus = true end
function methods:ClearFocus() self.focus = false; if focus == self then focus = nil end end
function methods:HasFocus() return self.focus == true end
function methods:SetVerticalScroll(value) self.scroll = value end
function methods:GetVerticalScroll() return self.scroll or 0 end
function methods:SetScrollChild(child) self.child = child end
function methods:SetStatusBarColor(...) self.barColor = {...} end
function methods:SetValue(value) self.value = value end
function methods:SetMinMaxValues(...) self.range = {...} end
function methods:SetTexture(value) self.texture = value end
function methods:SetBlendMode(value) self.blendMode = value end
function methods:SetVertexColor(...) self.vertexColor = {...} end
function methods:SetTextColor(...) self.textColor = {...} end
function methods:SetClampedToScreen(value) self.clamped = value end
function methods:StartMoving() self.moving = true end
function methods:StopMovingOrSizing() self.moving = false end
for _, key in ipairs({"SetAllPoints", "SetTexCoord", "SetColorTexture", "SetJustifyH", "SetJustifyV",
    "SetAutoFocus", "SetMaxLetters", "SetNumeric", "HighlightText", "SetFrameStrata", "SetMovable",
    "EnableMouse", "RegisterForDrag", "SetBackdrop", "SetBackdropColor", "SetBackdropBorderColor",
    "RegisterForClicks", "SetStatusBarTexture", "EnableMouseWheel"}) do methods[key] = function() end end
function CreateFrame(kind, name, parent, template)
    local frame = setmetatable({kind=kind, name=name, parent=parent, template=template,
        scripts={}, events={}, shown=true, children={}}, {__index=methods})
    if parent then parent.children[#parent.children+1] = frame end
    frames[#frames+1] = frame
    if name then _G[name] = frame end
    return frame
end
function methods:CreateFontString() return CreateFrame("FontString", nil, self) end
function methods:CreateTexture() return CreateFrame("Texture", nil, self) end
local animationMethods = {}
function methods:CreateAnimationGroup()
    return setmetatable({scripts={}, animations={}, plays=0}, {__index=animationMethods})
end
function animationMethods:CreateAnimation(kind)
    local animation = {}
    for _,key in ipairs({'FromAlpha','ToAlpha','Duration','Order'}) do
        animation['Set'..key] = function(self,value) self[key] = value end
    end
    animation.kind=kind
    self.animations[#self.animations+1] = animation
    return animation
end
function animationMethods:SetScript(key,callback) self.scripts[key] = callback end
function animationMethods:Play() self.plays=self.plays+1; self.playing=true end
function animationMethods:Stop()
    self.playing=false
    if self.scripts.OnStop then self.scripts.OnStop(self) end
end
function animationMethods:Finish()
    self.playing=false
    if self.scripts.OnFinished then self.scripts.OnFinished(self) end
end
UIParent = CreateFrame("Frame")
C_Container = {
    GetContainerNumSlots=function(bag) return bags[bag] and #bags[bag] or 0 end,
    GetContainerItemInfo=function(bag, slot)
        scans = (scans or 0) + 1
        return bags[bag][slot]
    end,
}
function GetItemInfo(item)
    local id = tonumber(item) or (type(item)=="string" and tonumber(item:match("item:(%d+)")))
    if not id then for key, data in pairs(itemData) do if data.name == item then id=key; break end end end
    local data = itemData[id]
    if data then return data.name, "|Hitem:"..id.."|h["..data.name.."]|h", 1, 1, 1, "", "", 20, "", data.icon end
end
C_Item = {GetItemInfo=GetItemInfo, RequestLoadItemDataByID=function(id) requestedItem = id end}
function C_Item.GetItemCount(id, includeBank, includeUses, includeReagentBank, includeAccountBank)
    local count = equippedItems[id] or 0
    for bag=0,5 do
        for _, item in ipairs(bags[bag] or {}) do
            if item.itemID==id then count=count+item.stackCount end
        end
    end
    if includeBank then count=count+(bankItems[id] or 0) end
    if includeReagentBank then count=count+(reagentBankItems[id] or 0) end
    if includeAccountBank then count=count+(accountBankItems[id] or 0) end
    return count
end
C_Timer = {After=function(_, callback) timers[#timers+1] = callback end}
function Tick() local queue=timers; timers={}; for _, callback in ipairs(queue) do callback() end end
function Fire(event, ...)
    for _, frame in ipairs(frames) do
        if frame.events[event] then frame.scripts.OnEvent(frame, event, ...) end
    end
end
function print(message) messages[#messages+1] = tostring(message) end
function hooksecurefunc(name, callback) hooks[name] = callback end
function HandleModifiedItemClick() end
function IsShiftKeyDown() return shifted end
function GetCursorInfo() return unpack(cursor or {}) end
function ClearCursor() cursor = nil end
GameTooltip = {SetOwner=function() end, SetHyperlink=function() end, AddLine=function() end,
    Show=function() end, Hide=function() end}
