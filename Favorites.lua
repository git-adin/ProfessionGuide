-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...

-- Only called by the explicit Plan route action, never by inventory/skill refreshes.
function ns.FavoritePlanRecipes(plan)
    if not plan then return "" end
    local ids,seen={},{}
    for _,step in ipairs(plan.steps) do
        for _,recipe in ipairs(step.recipes) do
            local id=recipe.spell
            if id and not seen[id] then ids[#ids+1]=id; seen[id]=true end
        end
    end
    if #ids==0 then return "" end
    local api=C_TradeSkillUI
    if not api or type(api.GetRecipeInfo)~="function" or type(api.SetRecipeFavorite)~="function"
        or type(api.IsRecipeFavorite)~="function" then
        return "Recipe favorites are unavailable in this client session."
    end
    local profession=ns.Safe(api.GetBaseProfessionInfo)
    if not Professions or ns.Safe(Professions.InLocalCraftingMode)~=true
        or type(profession)~="table" or profession.professionID~=ns.Professions[plan.slug].id then
        return "Open your "..ns.Professions[plan.slug].name.." profession window and click Plan route again to favorite learned recipes."
    end
    local added,existing,unlearned,unavailable=0,0,0,0
    for _,id in ipairs(ids) do
        local info=ns.Safe(api.GetRecipeInfo,id)
        if type(info)~="table" or info.recipeID~=id then unavailable=unavailable+1
        elseif info.learned~=true then unlearned=unlearned+1
        elseif ns.Safe(api.IsRecipeFavorite,id)==true then existing=existing+1
        else
            local ok=pcall(api.SetRecipeFavorite,id,true)
            if ok and ns.Safe(api.IsRecipeFavorite,id)==true then added=added+1
            else unavailable=unavailable+1 end
        end
    end
    local message="Recipe favorites: "..added.." added, "..existing.." already starred."
    if unlearned>0 then message=message.." "..unlearned.." unlearned skipped." end
    if unavailable>0 then message=message.." "..unavailable.." unavailable; retry with the profession open." end
    return message
end
