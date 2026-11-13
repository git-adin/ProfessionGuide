-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
function ns.FindChoice(slug,groupID,optionID)
    for _,group in ipairs(ns.Alternates[slug] or {}) do
        if group.id==groupID then
            for _,option in ipairs(group.options) do if option.id==optionID then return group,option end end
        end
    end
end
function ns.ActiveChoices(slug)
    return ns.db and ns.db.choices and ns.db.choices[slug] or {}
end
function ns.SelectedOption(slug,group,choices)
    local _,option=ns.FindChoice(slug,group.id,(choices or ns.ActiveChoices(slug))[group.id] or "default")
    return option or group.options[1]
end
function ns.GetGuideSteps(slug,choices)
    local steps={}
    for _,step in ipairs(ns.Guides[slug].steps) do steps[#steps+1]=step end
    for _,group in ipairs(ns.Alternates[slug] or {}) do
        local option=ns.SelectedOption(slug,group,choices)
        for _,block in ipairs(option.blocks) do
            local nextSteps={}
            for _,step in ipairs(steps) do
                if step.to<=block.from or step.from>=block.to then nextSteps[#nextSteps+1]=step end
            end
            for _,step in ipairs(block.steps) do nextSteps[#nextSteps+1]=step end
            steps=nextSteps
        end
    end
    table.sort(steps,function(a,b) return a.from<b.from end)
    return steps
end
function ns.GroupForStep(slug,step)
    if not step then return end
    for _,group in ipairs(ns.Alternates[slug] or {}) do
        for _,range in ipairs(group.ranges) do
            if step.to>range[1] and step.from<range[2] then return group end
        end
    end
end
function ns.MaterialDelta(before,after)
    if not before or not after then return "Choose a target to compare material totals." end
    local quantities,names={},{}
    for _,m in ipairs(before.materials) do quantities[m.name]=-m.quantity end
    for _,m in ipairs(after.materials) do quantities[m.name]=(quantities[m.name] or 0)+m.quantity end
    for name,amount in pairs(quantities) do if amount~=0 then names[#names+1]=name end end
    table.sort(names)
    local lines={}
    for _,name in ipairs(names) do
        local n=quantities[name]
        lines[#lines+1]=(n>0 and "Adds " or "Reduces ")..math.abs(n).." "..name
    end
    local description=#lines>0 and table.concat(lines,"; ") or "No material total changes for this target."
    if before.minimum or after.minimum then description=description..". Includes minimum estimates; actual use can be higher." end
    return description
end
function ns.CompareChoice(slug,group,option)
    local target=ns.db.targets[slug]
    if not target then return "Choose a target to compare material totals." end
    local choices={}; for k,v in pairs(ns.ActiveChoices(slug)) do choices[k]=v end
    choices[group.id]=option.id
    return ns.MaterialDelta(ns.Plan(slug,ns.player,target),ns.Plan(slug,ns.player,target,choices))
end
function ns.SetChoice(slug,groupID,optionID)
    local group,option=ns.FindChoice(slug,groupID,optionID)
    if not option then return false,"Unknown alternate." end
    if option.faction and ns.player.faction~=option.faction then return false,"This alternate is for "..option.faction.." only." end
    local before=ns.db.targets[slug] and ns.Plan(slug,ns.player,ns.db.targets[slug])
    ns.db.choices[slug]=ns.db.choices[slug] or {}
    ns.db.choices[slug][groupID]=optionID~="default" and optionID or nil
    local after=ns.db.targets[slug] and ns.Plan(slug,ns.player,ns.db.targets[slug])
    ns.choiceDelta=ns.MaterialDelta(before,after)
    local old=ns.selectedStep
    if old then
        for _,step in ipairs(ns.GetGuideSteps(slug)) do
            if step.from<=old.from and step.to>old.from then ns.routeSelection={slug=slug,to=step.to}; break end
        end
    end
    ns.showNotes=false
    ns.status="Recipe choice saved. Preview updated; farming goals were not changed."
    return true
end
