-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
local function safe(fn, ...)
    if type(fn)~="function" then return end
    local function pack(...) return {n=select("#",...),...} end
    local result=pack(pcall(fn, ...))
    if result[1] then return unpack(result,2,result.n) end
end
ns.Safe = safe
function ns.ReadCharacter()
    local out={level=safe(UnitLevel,"player") or 1, faction=safe(UnitFactionGroup,"player"), professions={}}
    local names, ids = {}, {}
    for slug, meta in pairs(ns.Professions) do
        ids[meta.id]=slug; names[meta.name]=slug
        local name = safe(C_Spell and C_Spell.GetSpellName,meta.spell) or safe(GetSpellInfo,meta.spell)
        if name then names[name]=slug end
    end
    local function add(id,name,rank,cap,icon)
        local slug=ids[id] or names[name]
        if slug and type(rank)=="number" and type(cap)=="number" then
            local previous=out.professions[slug]
            out.professions[slug]={name=name or ns.Professions[slug].name, rank=rank, cap=cap,
                icon=icon or (previous and previous.icon)}
        end
    end
    if GetProfessions and GetProfessionInfo then
        local indices={safe(GetProfessions)}
        -- These returns contain holes when primary professions are unlearned.
        for i=1,6 do
            if indices[i] then
                local name,icon,rank,cap,_,_,id=safe(GetProfessionInfo,indices[i])
                add(id,name,rank,cap,icon)
            end
        end
    end
    if C_SkillInfo and C_SkillInfo.GetSkillLineInfo then
        for i=1,safe(C_SkillInfo.GetNumSkillLines) or 0 do
            local s=safe(C_SkillInfo.GetSkillLineInfo,i)
            if s then
                if s.isHeader and s.isCollapsed then out.collapsed=true end
                if not s.isHeader then add(s.skillID,s.name,s.rank,s.maxRank) end
            end
        end
    elseif GetSkillLineInfo then
        for i=1,safe(GetNumSkillLines) or 0 do
            local name,header,collapsed,rank,_,_,cap,_,_,_,_,_,id=safe(GetSkillLineInfo,i)
            if header and collapsed then out.collapsed=true end
            if not header then add(id,name,rank,cap) end
        end
    end
    return out
end
