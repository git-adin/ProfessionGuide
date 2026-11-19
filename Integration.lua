-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...

local function GetFarmingTool()
    local api = ItemFarmingToolAPI
    if type(api) == "table" and type(api.GetTrackedGoals) == "function"
        and type(api.ApplyMinimumGoals) == "function" then
        return api
    end
    local isLoaded = C_AddOns and C_AddOns.IsAddOnLoaded or IsAddOnLoaded
    if isLoaded and isLoaded("ItemFarmingTool") then
        return nil, "Update ItemFarmingTool to enable export. The guide and shopping list remain available."
    end
    return nil, "ItemFarmingTool not loaded. The guide and shopping list remain available."
end

function ns.CanExport()
    local api, reason = GetFarmingTool()
    return api ~= nil, reason
end

function ns.ExportReview(plan)
    local previous = plan and ns.db.exports[plan.slug]
    local api = previous and GetFarmingTool()
    if not api then return end
    local needed = {}
    for _, material in ipairs(plan.materials) do
        if material.id then
            needed[material.id] = math.max(needed[material.id] or 0, material.quantity)
        end
    end
    local tracked = api.GetTrackedGoals()
    local names = {}
    for name, id in pairs(ns.ItemIDs) do names[id] = name end
    local lines = {}
    for id, quantity in pairs(previous) do
        local current = needed[id] or 0
        if current < quantity and tracked[id] and tracked[id] > current then
            lines[#lines + 1] = (names[id] or "Item " .. id) .. ": tracked " .. tracked[id] .. ", this route needs " .. current
        end
    end
    table.sort(lines)
    if #lines > 0 then
        return "Review previous farming goals (edit/remove manually; other plans may use them):\n" .. table.concat(lines, "\n")
    end
end

function ns.Export(plan)
    if not plan or not ns.db.targets[plan.slug] then return false, "Choose and apply a target first." end
    local api, reason = GetFarmingTool()
    if not api then return false, reason end
    if #plan.materials == 0 then return false, "There are no materials to export for this route." end

    local existing = api.GetTrackedGoals()
    local ok, errorMessage = api.ApplyMinimumGoals(plan.materials, true)
    if not ok then return false, errorMessage end

    local history = ns.db.exports[plan.slug] or {}
    for id, quantity in pairs(history) do
        if not existing[id] then history[id] = nil
        elseif existing[id] < quantity then history[id] = existing[id] end
    end
    for _, material in ipairs(plan.materials) do
        history[material.id] = math.max(history[material.id] or 0, material.quantity)
    end
    ns.db.exports[plan.slug] = history
    return true, "Exported material totals. Existing higher goals were preserved."
end
