-- SPDX-License-Identifier: GPL-3.0-or-later
local addon, ns = ...
function ns.LoadSettings()
    if ns.db then return end
    if type(ProfessionGuideDB)~="table" then ProfessionGuideDB={} end
    ns.db=ProfessionGuideDB
    local targets={}
    if type(ns.db.targets)=="table" then
        for slug,target in pairs(ns.db.targets) do
            if ns.Professions[slug] and ns.Integer(target,1,300) then targets[slug]=target end
        end
    end
    ns.db.targets=targets
    if not ns.Professions[ns.db.selected] then ns.db.selected=nil end
    ns.db.hidden=ns.db.hidden~=false -- stay quiet until first /pg
    local p=ns.db.position
    local points={TOPLEFT=true,TOP=true,TOPRIGHT=true,LEFT=true,CENTER=true,RIGHT=true,
        BOTTOMLEFT=true,BOTTOM=true,BOTTOMRIGHT=true}
    local function offset(v) return type(v)=="number" and v==v and math.abs(v)<100000 end
    if type(p)~="table" or not points[p.point] or not points[p.relativePoint] or not offset(p.x) or not offset(p.y) then ns.db.position=nil end
end
function ns.KnownProfessions()
    local list={}
    for _,slug in ipairs(ns.Order) do if ns.player.professions[slug] then list[#list+1]=slug end end
    return list
end
function ns.Refresh()
    ns.player=ns.ReadCharacter()
    if not ns.player.professions[ns.db.selected] then ns.db.selected=ns.KnownProfessions()[1] end
    ns.Render()
end
function ns.SetTarget(value)
    local slug=ns.db.selected
    if not slug or not ns.player.professions[slug] then return false,"Select a learned profession first." end
    local target=ns.Integer(value,1,300)
    if not target then return false,"Target must be a whole number from 1 to 300." end
    ns.db.targets[slug]=target
    return true,"Target saved. Review materials, then click Export if desired."
end
local function printMessage(message) print("|cff66d9b3ProfessionGuide:|r "..message) end
function ns.Command(message)
    local command,rest=(message or ""):match("^%s*(%S*)%s*(.-)%s*$")
    command=command:lower()
    if command=="hide" then ns.db.hidden=true
    elseif command=="target" then
        local _,info=ns.SetTarget(rest); printMessage(info)
    elseif command=="select" then
        local slug=rest:lower():gsub("%s+","-")
        if ns.player.professions[slug] then ns.db.selected=slug; ns.status=nil
        else printMessage("That profession is not detected. Use /pg and cycle the profession button.") end
    elseif command=="reset" then
        ns.db.position=nil; ns.db.hidden=false; ns.ApplyPosition()
    elseif command=="" or command=="show" then ns.db.hidden=false
    else printMessage("/pg show | hide | select <profession> | target <1-300> | reset"); return end
    ns.Refresh(); ns.Render(true)
end
local events=CreateFrame("Frame")
ns.events=events
events:RegisterEvent("ADDON_LOADED"); events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent",function(self,event,name)
    if event=="ADDON_LOADED" then
        if name==addon then ns.LoadSettings() end
    elseif event=="PLAYER_LOGIN" then
        ns.LoadSettings(); ns.player=ns.ReadCharacter(); ns.CreateUI()
        SlashCmdList.PROFESSIONGUIDE=ns.Command
        SLASH_PROFESSIONGUIDE1,SLASH_PROFESSIONGUIDE2="/pg","/professionguide"
        for _,e in ipairs({"SKILL_LINES_CHANGED","CHAT_MSG_SKILL","PLAYER_LEVEL_UP","PLAYER_ENTERING_WORLD","BAG_UPDATE_DELAYED","TRADE_SKILL_CLOSE"}) do self:RegisterEvent(e) end
        ns.Refresh()
    elseif ns.db and ns.frame then
        if ns.pending then return end
        ns.pending=true
        local function update() ns.pending=nil; ns.Refresh() end
        if C_Timer and C_Timer.After then C_Timer.After(0.1,update) else update() end
    end
end)
