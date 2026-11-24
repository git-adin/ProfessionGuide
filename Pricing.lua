-- SPDX-License-Identifier: GPL-3.0-or-later
local addon, ns = ...

local function validPrice(value)
    if issecretvalue and issecretvalue(value) then return end
    if type(value)=="number" and value>0 and value<math.huge then return value end
end

local function auctionatorAPI() return Auctionator and Auctionator.API and Auctionator.API.v1 end
local providers={
    {name="AuctionPriceLite",lowLabel="AH low (estimate)",quantityPricing=true,
        available=function() return AuctionPriceLite and type(AuctionPriceLite.GetItemPrice)=="function" end,
        quote=function(id) return AuctionPriceLite.GetItemPrice(id) end,
        scanTime=function() return ns.Safe(AuctionPriceLite.GetScanTime) end},
    {name="Auctionator",lowLabel="Last scanned buyout",
        available=function() local api=auctionatorAPI(); return api and type(api.GetAuctionPriceByItemID)=="function" end,
        quote=function(id) return auctionatorAPI().GetAuctionPriceByItemID(addon,id) end},
    {name="TradeSkillMaster",lowLabel="DBMinBuyout",averageLabel="DBMarket",
        available=function() return TSM_API and type(TSM_API.GetCustomPriceValue)=="function" end,
        quote=function(id)
            return ns.Safe(TSM_API.GetCustomPriceValue,"DBMinBuyout","i:"..id),
                ns.Safe(TSM_API.GetCustomPriceValue,"DBMarket","i:"..id)
        end},
    {name="Auctioneer",averageLabel="Market value",
        available=function() return AucAdvanced and AucAdvanced.API and type(AucAdvanced.API.GetMarketValue)=="function" end,
        quote=function(id)
            local _,link=ns.Safe(GetItemInfo,id)
            return nil,AucAdvanced.API.GetMarketValue(link or ("item:"..id))
        end},
}

local function quoteRecipe(recipe,provider)
    local cost={low=0,average=0,missingLow={},missingAverage={},source=provider.name,
        lowLabel=provider.lowLabel,averageLabel=provider.averageLabel}
    local count=0
    for _,material in ipairs(recipe.materials or {}) do
        local id=ns.ItemIDs[material.name]
        local low,average
        count=count+1
        if id then low,average=ns.Safe(provider.quote,id) end
        low,average=validPrice(low),validPrice(average)
        if low then cost.low=cost.low+low*material.quantity
        else cost.missingLow[#cost.missingLow+1]=material.name end
        if average then cost.average=cost.average+average*material.quantity
        else cost.missingAverage[#cost.missingAverage+1]=material.name end
    end
    cost.scannedAt=ns.Safe(provider.scanTime)
    cost.coverage=math.max(provider.lowLabel and count-#cost.missingLow or 0,
        provider.averageLabel and count-#cost.missingAverage or 0)
    return cost
end

local function stockRecipe(recipe,crafts,provider)
    local cost={low=0,stepLow=crafts and 0 or nil,missingLow={},missingStep={},missingAverage={},
        shortages={},source=provider.name,lowLabel="Scanned buyouts",stockVerified=true,
        scannedAt=ns.Safe(provider.scanTime)}
    local function add(material,quantity,scope)
        local id=ns.ItemIDs[material.name]
        local amount,found
        if id then amount,found=ns.Safe(AuctionPriceLite.GetItemCost,id,quantity) end
        amount=validPrice(amount)
        local missing=scope=="craft" and cost.missingLow or cost.missingStep
        if amount and type(found)=="number" and found>=quantity then return amount end
        missing[#missing+1]=material.name
        if (not crafts or scope=="step") and type(found)=="number" and found>=0 and found<quantity then
            cost.shortages[material.name]={found=found,needed=quantity}
        end
        return 0
    end
    for _,material in ipairs(recipe.materials or {}) do
        cost.low=cost.low+add(material,material.quantity,"craft")
        if crafts then cost.stepLow=cost.stepLow+add(material,material.quantity*crafts,"step") end
    end
    return cost
end

function ns.CraftCost(recipe,crafts)
    local best
    for _,provider in ipairs(providers) do
        if provider.available() then
            if provider.quantityPricing then
                local _,_,hasStock=ns.Safe(AuctionPriceLite.GetScanTime)
                if hasStock and type(AuctionPriceLite.GetItemCost)=="function" then
                    -- A known stock shortage must not fall back to an unverified unit quote.
                    return stockRecipe(recipe,crafts,provider)
                end
            end
            local cost=quoteRecipe(recipe,provider)
            -- Use one provider for the entire recipe; prefer greater coverage.
            if not best or cost.coverage>best.coverage then best=cost end
        end
    end
    return best
end

function ns.FormatCost(copper)
    copper=math.ceil(copper)
    local gold=math.floor(copper/10000)
    local silver=math.floor(copper/100)%100
    local coins=copper%100
    if gold>0 then return gold.."g "..silver.."s "..coins.."c" end
    if silver>0 then return silver.."s "..coins.."c" end
    return coins.."c"
end

function ns.CraftCostText(recipe,crafts)
    local cost=ns.CraftCost(recipe,crafts)
    if not cost then return "Craft cost: optional pricing addon not loaded (AuctionPriceLite, Auctionator, TradeSkillMaster or Auctioneer)." end
    local lines={}
    local function quote(label,value,missing,step,missingStep)
        if #missing>0 then
            return label..": incomplete (missing "..table.concat(missing,", ")..")."
        end
        local total=cost.stockVerified and step or value*(crafts or 1)
        return label..": "..ns.FormatCost(value).." per craft"
            ..(crafts and ((missingStep and #missingStep>0) and "; step stock incomplete"
                or ("; about "..ns.FormatCost(total).." for "..crafts.." crafts")) or "").."."
    end
    if cost.lowLabel then lines[#lines+1]=quote("Craft cost, "..cost.lowLabel,cost.low,cost.missingLow,cost.stepLow,cost.missingStep) end
    if cost.averageLabel then
        lines[#lines+1]=quote(cost.averageLabel,cost.average,cost.missingAverage)
    end
    local stamp=type(cost.scannedAt)=="number" and cost.scannedAt>0 and cost.scannedAt<math.huge
        and ns.Safe(date,"%m/%d %H:%M",cost.scannedAt)
    lines[#lines+1]=cost.source..(stamp and (" scan "..stamp) or " saved prices")
        ..". Owned materials included; prices may have changed."
    if (recipe.yield or 1)>1 then lines[#lines+1]="Each craft makes "..recipe.yield.." items." end
    return table.concat(lines,"\n")
end

function ns.InitPricing()
    if ns.pricingRegistered or not EventRegistry or type(EventRegistry.RegisterCallback)~="function" then return end
    EventRegistry:RegisterCallback("AuctionPriceLite.PricesChanged",function()
        if ns.pricingPending then return end
        ns.pricingPending=true
        local function update()
            ns.pricingPending=nil
            if ns.db and ns.player and ns.frame and ns.frame:IsShown() then ns.Render() end
        end
        if C_Timer and C_Timer.After then C_Timer.After(0.1,update) else update() end
    end,ns)
    ns.pricingRegistered=true
end
