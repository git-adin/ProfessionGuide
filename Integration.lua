-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
function ns.CanExport()
    return SlashCmdList and type(SlashCmdList.ITEMFARMINGTOOL)=="function"
        and type(ItemFarmingToolDB)=="table" and type(ItemFarmingToolDB.items)=="table"
end
function ns.ExportReview(plan)
    if not plan or not ns.CanExport() then return end
    local previous=ns.db.exports[plan.slug]
    if not previous then return end
    local needed,tracked={},{}
    for _,m in ipairs(plan.materials) do needed[m.id]=m.quantity end
    for _,entry in ipairs(ItemFarmingToolDB.items) do tracked[entry.id]=entry.goal end
    local names={}
    for name,id in pairs(ns.ItemIDs) do names[id]=name end
    local lines={}
    for id,quantity in pairs(previous) do
        local current=needed[id] or 0
        if current<quantity and tracked[id] and tracked[id]>current then
            lines[#lines+1]=(names[id] or "Item "..id)..": tracked "..tracked[id]..", this route needs "..current
        end
    end
    table.sort(lines)
    if #lines>0 then return "Review previous farming goals (edit/remove manually; other plans may use them):\n"..table.concat(lines,"\n") end
end
function ns.Export(plan)
    if not plan or not ns.db.targets[plan.slug] then return false,"Choose and apply a target first." end
    if not ns.CanExport() then return false,"ItemFarmingTool is unavailable. The guide works without it." end
    if #plan.materials==0 then return false,"There are no materials to export for this route." end
    -- Preflight the entire list. Never partly export a list that exceeds capacity.
    local existing, total={},#ItemFarmingToolDB.items
    for _,entry in ipairs(ItemFarmingToolDB.items) do existing[entry.id]=entry.goal end
    for _,m in ipairs(plan.materials) do
        if not m.id or not ns.Integer(m.quantity,1,999999) then return false,"Cannot export an unresolved item or invalid quantity." end
        if not existing[m.id] then total=total+1 end
    end
    if total>100 then return false,"ItemFarmingTool would exceed 100 items. Remove some goals first." end
    for _,m in ipairs(plan.materials) do
        -- Preserve higher goals and unrelated manual entries. Repeated exports
        -- set the same minimum goal rather than adding another batch each click.
        if not existing[m.id] or existing[m.id]<m.quantity then
            SlashCmdList.ITEMFARMINGTOOL("add "..m.id.." "..m.quantity)
        end
    end
    local history=ns.db.exports[plan.slug] or {}
    for id,quantity in pairs(history) do
        if not existing[id] then history[id]=nil
        elseif existing[id]<quantity then history[id]=existing[id] end
    end
    for _,m in ipairs(plan.materials) do history[m.id]=math.max(history[m.id] or 0,m.quantity) end
    ns.db.exports[plan.slug]=history
    SlashCmdList.ITEMFARMINGTOOL("show")
    return true,"Exported material totals. Existing higher goals were preserved."
end
