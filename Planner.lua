-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
function ns.Integer(value, minimum, maximum)
    local n=tonumber(value)
    if n and n==n and n%1==0 and n>=minimum and n<=maximum then return n end
end
function ns.BagCount(name)
    local id=ns.ItemIDs[name]
    local count=id and ns.Safe(C_Item and C_Item.GetItemCount or GetItemCount,id,false,false,false,false)
    return type(count)=="number" and math.max(0,count) or 0
end
function ns.Plan(slug, player, target)
    local guide, meta=ns.Guides[slug], ns.Professions[slug]
    local skill=player.professions[slug]
    if not skill then return nil,"Profession not detected. Learn it or expand the Skills panel." end
    if not ns.Integer(target,1,300) then return nil,"Choose a whole-number target from 1 to 300." end
    local plan={steps={},materials={},warnings={},target=target,rank=skill.rank,slug=slug}
    if target<=skill.rank then plan.complete=true; return plan end
    local limit=math.min(target,guide.cap)
    if target>guide.cap then plan.warnings[#plan.warnings+1]="Source coverage ends at "..guide.cap.."; later steps are unavailable." end
    if target>225 then plan.warnings[#plan.warnings+1]="Higher-level source routes are provisional; check recipes before buying." end
    if slug=="lockpicking" then
        local cap=math.min(300,player.level*5)
        if target>cap then plan.warnings[#plan.warnings+1]="Character level "..math.ceil(target/5).." is needed for this target (current cap "..cap..")." end
    else
        for _,r in ipairs(ns.RankRequirements(slug)) do
            if target>r.cap and skill.cap<=r.cap then
                local hint="Train "..r.name..": skill "..r.skill..", character level "..r.level.."."
                if player.level<r.level then hint=hint.." Character level is too low." end
                plan.warnings[#plan.warnings+1]=hint
            end
        end
    end
    local demand, supply, conversions={},{},{}
    local imperial={ ["Imperial Plate Belt"]=20,["Imperial Plate Bracers"]=20,
        ["Imperial Plate Boots"]=40,["Imperial Plate Leggings"]=60 }
    for _,s in ipairs(guide.steps) do
        for _,r in ipairs(s.recipes or {}) do conversions[r.name]=r end
        if s.to>skill.rank and s.from<limit then
            local lo,hi=math.max(skill.rank,s.from),math.min(limit,s.to)
            local step={from=lo,to=hi,action=s.action,recipes={}}
            local zone=player.faction=="Horde" and s.horde or s.alliance
            if zone then step.action=(step.action or "").." Location: "..zone.."." end
            for _,r in ipairs(s.recipes or {}) do
                local crafts=math.ceil(r.crafts*(hi-lo)/(s.to-s.from))
                step.recipes[#step.recipes+1]={name=r.name,crafts=crafts}
                supply[r.name]=(supply[r.name] or 0)+crafts*(r.yield or 1)
                for _,m in ipairs(r.materials) do demand[m.name]=(demand[m.name] or 0)+math.ceil(m.quantity*crafts) end
                if slug=="blacksmithing" and imperial[r.name] and ns.Safe(IsPlayerSpell,r.spell)~=true then
                    demand["Thorium Bar"]=(demand["Thorium Bar"] or 0)+imperial[r.name]
                end
            end
            plan.steps[#plan.steps+1]=step
        end
    end
    if slug=="cooking" and target>225 and skill.cap<=225 then
        demand["Giant Egg"],demand["Zesty Clam Meat"],demand["Alterac Swiss"]=12,10,20
        plan.warnings[#plan.warnings+1]="Artisan Cooking quest supplies are included."
    end
    if slug=="blacksmithing" and target>240 then
        plan.warnings[#plan.warnings+1]="Imperial Plate: level 50 required; quest skill gates are unverified. Recipe quest bars are included unless the recipe is detected as known."
    end
    if ((slug=="engineering" and target>200) or (slug=="leatherworking" and target>205)) and player.level<35 then
        plan.warnings[#plan.warnings+1]="This route uses Artisan recipes before 225: character level 35 is required."
    end
    -- Net route outputs before expanding missing intermediates. Base leather is
    -- purchased as leather; do not assume the player wants to convert scraps.
    for name,amount in pairs(supply) do demand[name]=math.max(0,(demand[name] or 0)-amount) end
    if slug=="tailoring" then
        conversions["Bolt of Runecloth"]={yield=1,materials={{name="Runecloth",quantity=5}}}
    end
    local raw, available={},{}
    local function expand(name,amount,path)
        if amount<=0 then return end
        local r=conversions[name]
        if name=="Light Leather" or name=="Medium Leather" or name=="Heavy Leather" then r=nil end
        if r and not path[name] then
            if available[name]==nil then available[name]=ns.BagCount(name) end
            local used=math.min(amount,available[name])
            available[name]=available[name]-used; amount=amount-used
            local crafts=math.ceil(amount/(r.yield or 1))
            local branch={}; for k,v in pairs(path) do branch[k]=v end; branch[name]=true
            for _,m in ipairs(r.materials) do expand(m.name,math.ceil(crafts*m.quantity),branch) end
        else raw[name]=(raw[name] or 0)+amount end
    end
    for name,amount in pairs(demand) do expand(name,amount,{}) end
    for name,amount in pairs(raw) do
        if amount>0 then plan.materials[#plan.materials+1]={name=name,id=ns.ItemIDs[name],quantity=amount,owned=ns.BagCount(name)} end
    end
    table.sort(plan.materials,function(a,b) return a.name<b.name end)
    return plan
end
