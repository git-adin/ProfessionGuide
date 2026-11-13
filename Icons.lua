-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
local PREFIX="Interface\\Icons\\"
local professionArt={
    alchemy="Trade_Alchemy",blacksmithing="Trade_BlackSmithing",enchanting="Trade_Engraving",
    engineering="Trade_Engineering",leatherworking="Trade_LeatherWorking",tailoring="Trade_Tailoring",
    mining="Trade_Mining",herbalism="Trade_Herbalism",skinning="INV_Misc_Pelt_Wolf_01",
    ["first-aid"]="Spell_Holy_SealOfSacrifice",cooking="INV_Misc_Food_15",
    fishing="Trade_Fishing",lockpicking="Spell_Nature_MoonKey",
}
function ns.ValidIcon(value)
    if type(value)=="number" and value>0 then return value end
    if type(value)=="string" and value~="" then return value end
end
function ns.SpellIcon(id)
    if not id or id==0 then return end
    local icon=ns.ValidIcon(ns.Safe(C_Spell and C_Spell.GetSpellTexture,id))
        or ns.ValidIcon(ns.Safe(GetSpellTexture,id))
    if not icon then local _,_,texture=ns.Safe(GetSpellInfo,id); icon=ns.ValidIcon(texture) end
    return icon or (ns.RecipeIcons and ns.RecipeIcons[id])
end
function ns.RecipeIcon(id)
    -- Forever can return a valid default/logo texture for legacy recipe spells.
    -- Prefer the mapped recipe artwork; numeric validity alone cannot identify
    -- these placeholders. Profession spells still use their live client icons.
    return ns.ValidIcon(ns.RecipeIcons and ns.RecipeIcons[id]) or ns.SpellIcon(id)
end
function ns.ProfessionIcon(slug)
    local meta=ns.Professions[slug]
    local skill=ns.player and ns.player.professions[slug]
    return ns.ValidIcon(skill and skill.icon) or (meta and ns.SpellIcon(meta.spell))
        or PREFIX..(professionArt[slug] or "INV_Misc_Book_09")
end
function ns.ItemIcon(id)
    if not id then return end
    local icon=ns.ValidIcon(ns.Safe(C_Item and C_Item.GetItemIconByID,id))
        or ns.ValidIcon(ns.Safe(GetItemIcon,id))
    if not icon then
        local _,_,_,_,texture=ns.Safe(C_Item and C_Item.GetItemInfoInstant or GetItemInfoInstant,id)
        icon=ns.ValidIcon(texture)
    end
    if not icon then
        local _,_,_,_,_,_,_,_,_,texture=ns.Safe(C_Item and C_Item.GetItemInfo or GetItemInfo,id)
        icon=ns.ValidIcon(texture)
    end
    if not icon then
        -- One request per item per session; receipt refreshes all visible uses.
        ns.itemRequested=ns.itemRequested or {}
        if not ns.itemRequested[id] then
            ns.itemRequested[id]=true
            ns.Safe(C_Item and C_Item.RequestLoadItemDataByID,id)
        end
    end
    return icon
end
function ns.IconTag(icon,size)
    return "|T"..tostring(icon)..":"..(size or 16)..":"..(size or 16)..":0:0|t "
end
function ns.StepIcon(slug,step)
    for _,s in ipairs(ns.GetGuideSteps(slug)) do
        if s.from<=step.from and s.to>=step.to then
            for _,r in ipairs(s.recipes or {}) do
                local icon=ns.RecipeIcon(r.spell)
                if icon then return icon end
            end
            break
        end
    end
    return ns.ProfessionIcon(slug)
end
