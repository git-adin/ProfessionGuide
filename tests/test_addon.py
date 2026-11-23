"""Run the shipped Lua 5.1 files with a deterministic UI/inventory harness."""
from pathlib import Path
import sys, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'.tools'))
sys.path.insert(0,str(ROOT/'.tools'))
from lupa.lua51 import LuaRuntime

FILES=['Data.lua','Routes.lua','Character.lua','Icons.lua','Choices.lua','Planner.lua','Favorites.lua','Pricing.lua','Trainers.lua','Integration.lua','UI.lua','Minimap.lua','ProfessionButton.lua','Core.lua']

class AddonTests(unittest.TestCase):
    def setUp(self):
        self.start_session()

    def start_session(self, farming_tool=None):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'tests/wow_mock.lua').read_text())
        self.lua.execute(r'''
            function UnitLevel() return level or 20 end
            function UnitFactionGroup() return 'Alliance' end
            skills={{skillID=171,name='Alchemy',rank=1,maxRank=75}}
            C_SkillInfo={GetNumSkillLines=function() return #skills end,
                GetSkillLineInfo=function(i) return skills[i] end}
            GetItemCount=function(id) return owned and owned[id] or 0 end
            C_Item.GetItemCount=GetItemCount
            local mt=getmetatable(UIParent).__index
            function mt:GetStringHeight()
                local value=self:GetText():gsub('|c%x%x%x%x%x%x%x%x',''):gsub('|r','')
                local lines=0
                for part in (value..'\n'):gmatch('(.-)\n') do
                    lines=lines+math.max(1,math.ceil(#part*7/(self.width or 1000)))
                end
                return lines*14
            end
            function mt:SetEnabled(value) self.enabled=value end
            UISpecialFrames={}
        ''')
        if farming_tool is not None:
            ift = self.lua.table()
            self.lua.globals().ift = ift
            for name in ['Core.lua', 'UI.lua']:
                self.lua.execute((farming_tool / name).read_text(encoding='utf-8'), 'ItemFarmingTool', ift)
            self.check("assert(ItemFarmingToolAPI==nil); Fire('ADDON_LOADED','ItemFarmingTool'); assert(ItemFarmingToolAPI)")
        ns=self.lua.table(); self.lua.globals().ns=ns
        for name in FILES: self.lua.execute((ROOT/name).read_text(encoding='utf-8'),'ProfessionGuide',ns)
        self.check("Fire('ADDON_LOADED','ProfessionGuide'); Fire('PLAYER_LOGIN')")

    def check(self,code): self.lua.execute(code)

    def start_paired_session(self):
        folder = ROOT.parent / 'ItemFarmingTool/ItemFarmingTool'
        if not folder.exists():
            self.skipTest('Optional sibling ItemFarmingTool source unavailable')
        self.start_session(farming_tool=folder)

    def install_farming_tool_spy(self):
        self.check('''batches={}; goals={}
            ItemFarmingToolAPI={
                GetTrackedGoals=function()
                    local snapshot={}
                    for id,quantity in pairs(goals) do snapshot[id]=quantity end
                    return snapshot
                end,
                ApplyMinimumGoals=function(materials,showTracker)
                    batches[#batches+1]={materials=materials,showTracker=showTracker}
                    if rejectBatch then return false,rejectBatch end
                    for _,material in ipairs(materials) do
                        goals[material.id]=math.max(goals[material.id] or 0,material.quantity)
                    end
                    return true
                end,
            }
        ''')

    def test_professions_button_late_load_and_open_only(self):
        self.check('''assert(ns.professionButton==nil)
            ProfessionsFrame=CreateFrame('Frame',nil,UIParent)
            ProfessionsFrame.BookPage=CreateFrame('Frame',nil,ProfessionsFrame)
            ProfessionsFrame.CraftingPage=CreateFrame('Frame',nil,ProfessionsFrame)
            ProfessionsFrame.CraftingPage:SetFrameLevel(100)
            ProfessionsFrame.CraftingPage:Hide()
            Fire('ADDON_LOADED','Blizzard_Professions')
            local b=ns.professionButton
            assert(b and b.parent==ProfessionsFrame and b:GetFrameLevel()>100)
            Fire('ADDON_LOADED','AnotherAddon'); ns.InitProfessionButton()
            assert(ns.professionButton==b)
            ns.Command('hide'); b.scripts.OnClick(b)
            assert(ns.frame:IsShown() and ns.db.selected=='alchemy')
            assert(ns.plan==nil and next(ns.db.targets)==nil and next(ns.db.exports)==nil)
            skills[2]={skillID=164,name='Blacksmithing',rank=130,maxRank=150}
            ProfessionsFrame.CraftingPage:Show(); ProfessionsFrame.selectedSkillLine=164
            b.scripts.OnClick(b)
            assert(ns.db.selected=='blacksmithing' and ns.frame:IsShown())
            b.scripts.OnClick(b); assert(ns.frame:IsShown())
            assert(ns.plan==nil and next(ns.db.targets)==nil and next(ns.db.exports)==nil)
            ProfessionsFrame:Hide(); assert(not b:IsShown())''')

    def test_professions_button_available_at_login(self):
        self.check('''ProfessionsBookFrame=CreateFrame('Frame',nil,UIParent)
            Fire('PLAYER_LOGIN')
            assert(ns.professionButton.parent==ProfessionsBookFrame)''')

    def test_plan_route_favorites_only_learned_chosen_recipes(self):
        self.check('''skills={{skillID=164,name='Blacksmithing',rank=130,maxRank=150}}; ns.Refresh()
            ns.SetChoice('blacksmithing','bronze','warhammer')
            favorites={}; writes={}; infos={}
            Professions={InLocalCraftingMode=function() return true end}
            C_TradeSkillUI={GetBaseProfessionInfo=function() return {professionID=164} end,
                GetRecipeInfo=function(id) return infos[id] end,
                IsRecipeFavorite=function(id) return favorites[id]==true end,
                SetRecipeFavorite=function(id,value) assert(value==true); writes[#writes+1]=id; favorites[id]=value end}
            ns.SetTarget(150); ns.Render()
            local id=ns.plan.steps[1].recipes[1].spell
            assert(id==9985)
            infos[id]={recipeID=id,learned=true}
            local other=ns.plan.steps[2].recipes[1].spell
            infos[other]={recipeID=other,learned=false}
            assert(#writes==0)
            ns.targetInput:SetText('150'); ns.applyButton.scripts.OnClick()
            assert(#writes==1 and writes[1]==9985)
            assert(ns.status:find('1 added') and ns.status:find('1 unlearned'))
            ns.applyButton.scripts.OnClick(); assert(#writes==1)
            assert(ns.status:find('1 already starred'))
            ns.Refresh(); Fire('BAG_UPDATE_DELAYED'); Tick(); assert(#writes==1)
            ns.targetInput:SetText('bad'); ns.applyButton.scripts.OnClick(); assert(#writes==1)
            assert(next(ns.db.exports)==nil)''')

    def test_favorites_deduplicate_failures_and_wrong_profession(self):
        self.check('''local p={slug='alchemy',steps={{recipes={{spell=1},{spell=1},{spell=2},{spell=3}}}}}
            assert(ns.FavoritePlanRecipes(p):find('unavailable'))
            local writes=0
            Professions={InLocalCraftingMode=function() return localMode end}
            C_TradeSkillUI={GetBaseProfessionInfo=function() return {professionID=professionID} end,
                GetRecipeInfo=function(id) return {recipeID=id,learned=true} end,
                IsRecipeFavorite=function() return false end,
                SetRecipeFavorite=function() writes=writes+1; error('unavailable') end}
            localMode=true; professionID=164
            assert(ns.FavoritePlanRecipes(p):find('Open your Alchemy')); assert(writes==0)
            professionID=171; localMode=false
            assert(ns.FavoritePlanRecipes(p):find('Open your Alchemy')); assert(writes==0)
            localMode=true
            assert(ns.FavoritePlanRecipes(p):find('3 unavailable')); assert(writes==3)
            assert(ns.FavoritePlanRecipes({slug='alchemy',steps={}})=='')''')

    def test_craft_cost_arithmetic_missing_prices_and_optional_provider(self):
        self.check('''local r={yield=2,materials={{name='Bronze Bar',quantity=5},{name='Coarse Grinding Stone',quantity=2}}}
            assert(ns.CraftCost(r)==nil)
            assert(ns.CraftCostText(r):find('optional pricing addon not loaded'))
            quotes={[2841]={101,150},[3478]={25,40}}
            AuctionPriceLite={GetItemPrice=function(id) return unpack(quotes[id] or {}) end,
                GetScanTime=function() return 10000 end}
            local c=ns.CraftCost(r); assert(c.low==555 and c.average==830)
            assert(#c.missingLow==0 and c.scannedAt==10000)
            local t=ns.CraftCostText(r,16)
            assert(t:find('5s 55c per craft') and t:find('88s 80c for 16 crafts'))
            assert(t:find('Each craft makes 2') and t:find('Owned materials included'))
            assert(ns.FormatCost(10001)=='1g 0s 1c' and ns.FormatCost(0.5)=='1c')
            quotes[3478]={0,0/0}; c=ns.CraftCost(r)
            assert(c.missingLow[1]=='Coarse Grinding Stone' and #c.missingAverage==1)
            assert(ns.CraftCostText(r):find('incomplete'))
            AuctionPriceLite.GetItemPrice=function() error('provider error') end
            assert(#ns.CraftCost(r).missingLow==2)''')

    def test_recipe_cost_refresh_does_not_export_or_favorite(self):
        self.check('''local callbacks={}; local registrations=0
            EventRegistry={RegisterCallback=function(_,event,callback)
                registrations=registrations+1; callbacks[event]=callback end}
            local price=100
            AuctionPriceLite={GetItemPrice=function() return price,price*2 end}
            ns.InitPricing(); ns.InitPricing(); assert(registrations==1)
            ns.Command('show'); ns.SetTarget(5); ns.Render()
            local before=ns.costCards[1].rows[1].total:GetText()
            assert(ns.costCards[1].footer:GetText():find('4 crafts'))
            assert(not ns.detailText:GetText():find('Craft cost'))
            local favorites=0; ns.FavoritePlanRecipes=function() favorites=favorites+1 end
            price=200; callbacks['AuctionPriceLite.PricesChanged'](); Tick()
            assert(ns.costCards[1].rows[1].total:GetText()~=before and favorites==0)
            assert(next(ns.db.exports)==nil)
            ns.Command('hide'); callbacks['AuctionPriceLite.PricesChanged'](); Tick()
            assert(not ns.frame:IsShown())''')

    def test_optional_pricing_providers_and_coverage_fallback(self):
        self.check('''local r={materials={{name='Bronze Bar',quantity=5},{name='Coarse Grinding Stone',quantity=2}}}
            TSM_API={GetCustomPriceValue=function(source,item)
                assert(item=='i:2841' or item=='i:3478')
                if source=='DBMinBuyout' then return 100 end
                assert(source=='DBMarket'); return 150 end}
            local c=ns.CraftCost(r); assert(c.source=='TradeSkillMaster' and c.low==700 and c.average==1050)
            assert(ns.CraftCostText(r):find('DBMarket'))
            AuctionPriceLite={GetItemPrice=function() return nil end}
            assert(ns.CraftCost(r).source=='TradeSkillMaster')
            TSM_API=nil; AuctionPriceLite=nil
            local queried={}
            AucAdvanced={API={GetMarketValue=function(link)
                queried[link]=true; return 200,99 end}}
            c=ns.CraftCost(r); assert(c.source=='Auctioneer' and c.average==1400)
            assert(queried['item:2841'] and queried['item:3478'])
            assert(ns.CraftCostText(r):find('Market value') and not ns.CraftCostText(r):find('AH low'))
            AucAdvanced=nil
            Auctionator={API={v1={GetAuctionPriceByItemID=function(caller,id)
                assert(caller=='ProfessionGuide' and (id==2841 or id==3478)); return 50 end}}}
            c=ns.CraftCost(r); assert(c.source=='Auctionator' and c.low==350)
            assert(ns.CraftCostText(r):find('Last scanned buyout'))
            Auctionator=nil
            assert(ns.CraftCost(r)==nil)
            ns.Command('show'); ns.SetTarget(5); ns.Render()
            assert(ns.plan and ns.frame:IsShown() and ns.costCards[1].footer:GetText():find('No pricing data provider'))''')

    def test_actual_auctionpricelite_public_api(self):
        source=ROOT.parent/'checkouts/AuctionPriceLite/AuctionPriceLite/Core.lua'
        if not source.exists(): self.skipTest('Optional AuctionPriceLite checkout unavailable')
        self.check('''GetCurrentRegion=function() return 1 end
            C_GameRules={GetCurrentGameModeRecordID=function() return 15 end}
            Enum.TooltipDataType={Item=0}
            TooltipDataProcessor={AddTooltipPostCall=function() end}
            EventRegistry={RegisterCallback=function() end,TriggerEvent=function() end}
            AuctionPriceLiteDB={snapshots={['1:15:Alliance']={prices={[2841]=101,[3478]=25},
                averages={[2841]=150,[3478]=40},scannedAt=10000,count=2}}}''')
        self.lua.execute(source.read_text(encoding='utf-8'),'AuctionPriceLite',self.lua.table())
        self.check('''Fire('ADDON_LOADED','AuctionPriceLite'); Fire('PLAYER_ENTERING_WORLD')
            local c=ns.CraftCost({materials={{name='Bronze Bar',quantity=5},{name='Coarse Grinding Stone',quantity=2}}})
            assert(c.source=='AuctionPriceLite' and c.low==555 and c.average==830 and c.scannedAt==10000)''')

    def test_training_notes_filter_faction_and_hide_rows(self):
        self.check('''skills={{skillID=164,name='Blacksmithing',rank=131,maxRank=150}}; ns.Refresh()
            ns.player.faction='Horde'; ns.showNotes=true; ns.Render()
            assert(ns.trainingHeader:GetText():find('Horde') and ns.trainingHeader:GetText():find('Ready to train'))
            assert(ns.trainingRows[1].label:GetText():find('Saru Steelfury'))
            assert(not ns.trainingRows[1].label:GetText():find('Bengus'))
            assert(ns.trainingRows[2].label:GetText():find('Brikk'))
            assert(not ns.trainingRows[3]:IsEnabled())
            ns.player.faction='Alliance'; ns.Render()
            assert(ns.trainingRows[1].label:GetText():find('Bengus'))
            ns.player.faction=nil; ns.Render()
            assert(ns.trainingHeader:GetText():find('Only neutral'))
            assert(ns.trainingRows[1].label:GetText():find('Brikk'))
            assert(not ns.trainingRows[3]:IsShown())
            ns.showNotes=false; ns.Render()
            assert(not ns.trainingHeader:IsShown() and not ns.trainingRows[1]:IsShown())
            for slug,entries in pairs(ns.Trainers) do
                for _,entry in ipairs(entries) do
                    assert(entry.name and entry.location and entry.role)
                    if entry.map then assert(entry.x>0 and entry.x<100 and entry.y>0 and entry.y<100) end
                end
            end''')

    def test_trainer_pin_success_failure_and_faction_guards(self):
        self.check('''ns.player.faction='Horde'
            local entry=ns.TrainersFor('blacksmithing')[1]
            local pins,opens=0,0
            UiMapPoint={CreateFromCoordinates=function(map,x,y)
                assert(map==1454 and x==82.3/100 and y==22.8/100)
                return {uiMapID=map,x=x,y=y} end}
            C_Map={CanSetUserWaypointOnMap=function() return allowed end,
                SetUserWaypoint=function(point) pins=pins+1; return pinResult end,
                OpenWorldMap=function(map) assert(map==1454); opens=opens+1 end}
            C_SuperTrack={SetSuperTrackedUserWaypoint=function(value) assert(value); tracked=true end}
            allowed=true; pinResult=true
            local ok,message=ns.PinTrainer(entry)
            assert(ok and message:find('Saru') and pins==1 and opens==1 and tracked)
            InCombatLockdown=function() return true end
            assert(ns.PinTrainer(entry)); assert(pins==2 and opens==1)
            allowed=false; assert(not ns.PinTrainer(entry)); assert(pins==2)
            allowed=true; pinResult=false; assert(not ns.PinTrainer(entry)); assert(opens==1)
            ns.player.faction='Alliance'; assert(not ns.PinTrainer(entry)); assert(pins==3)
            C_Map=nil; ns.player.faction='Horde'; assert(not ns.PinTrainer(entry))
            assert(next(ns.db.targets)==nil and next(ns.db.exports)==nil)''')

    def test_guide_button_above_title_border_and_first_aid_switch(self):
        self.check('''ProfessionsFrame=CreateFrame('Frame',nil,UIParent)
            local shown=0
            ProfessionsFrame:SetScript('OnShow',function() shown=shown+1 end)
            for _,key in ipairs({'BookPage','CraftingPage','NineSlice','TitleContainer','CloseButton'}) do
                ProfessionsFrame[key]=CreateFrame('Frame',nil,ProfessionsFrame)
            end
            ProfessionsFrame.BookPage:SetFrameLevel(100)
            ProfessionsFrame.CraftingPage:SetFrameLevel(100)
            ProfessionsFrame.NineSlice:SetFrameLevel(500)
            ProfessionsFrame.TitleContainer:SetFrameLevel(510)
            ProfessionsFrame.CloseButton:SetFrameLevel(510)
            Fire('ADDON_LOADED','Blizzard_Professions')
            local b=ns.professionButton
            assert(b:GetFrameLevel()>510 and b:IsShown())
            local point,relative,relativePoint,x=b:GetPoint()
            assert(point=='RIGHT' and relative==ProfessionsFrame.CloseButton and relativePoint=='LEFT' and x<0)
            ProfessionsFrame.NineSlice:SetFrameLevel(750)
            ProfessionsFrame:GetScript('OnSizeChanged')(ProfessionsFrame)
            assert(b:GetFrameLevel()>750)
            b:Hide(); ProfessionsFrame:GetScript('OnShow')(ProfessionsFrame)
            assert(b:IsShown() and shown==1)
            ProfessionsFrame.TitleContainer:SetFrameLevel(800)
            ProfessionsFrame.CraftingPage:GetScript('OnShow')(ProfessionsFrame.CraftingPage)
            assert(b:GetFrameLevel()>800)
            skills={{skillID=129,name='First Aid',rank=106,maxRank=150}}
            ProfessionsFrame.selectedSkillLine=129
            b:GetScript('OnClick')(b)
            assert(ns.db.selected=='first-aid' and ns.frame:IsShown())
            assert(next(ns.db.targets)==nil and next(ns.db.exports)==nil)
            ProfessionsFrame:Hide(); assert(not b:IsShown())''')

    def test_workshop_cost_table_and_shopping_hierarchy(self):
        self.check('''skills={{skillID=165,name='Leatherworking',rank=205,maxRank=300}}
            owned={[4304]=4}; ns.Refresh(); ns.Command('show')
            AuctionPriceLite={GetItemPrice=function() return 100,200 end}
            ns.SetTarget(225); ns.Render()
            assert(ns.recipeText:GetText()=='Nightscape Pants')
            local card=ns.costCards[1]
            assert(card:IsShown() and card.each:GetText()=='Each craft' and card.total:GetText()=='This step')
            assert(card.rows[1].each:GetText()=='18s 0c')
            assert(card.rows[1].total:GetText():find('4g 32s 0c'))
            assert(card.rows[2].total:GetText():find('8g 64s 0c'))
            assert(not ns.detailText:GetText():find('AuctionPriceLite'))
            assert(card.helpRows[3][1]=='Owned materials' and card.helpRows[3][2]=='Included in value')
            assert(ns.tableHead[2].title=='In bags' and ns.tableHead[3].title=='Required' and ns.tableHead[4].title=='To get')
            for _,row in ipairs(ns.materialRows) do
                if row.itemID==4304 then
                    assert(row.have:GetText()=='4' and row.need:GetText()=='336' and row.short:GetText():find('332'))
                end
            end
            AuctionPriceLite.GetItemPrice=function(id)
                if id~=ns.ItemIDs['Silken Thread'] then return 100,200 end end
            ns.Render()
            assert(card.rows[1].each:GetText():find('Missing prices') and card.rows[1].total:GetText():find('—'))
            assert(#card.missingPrices==1 and card.missingPrices[1]=='Silken Thread')
            ns.showNotes=true; ns.Render(); assert(not card:IsShown())
            ns.showNotes=false; ns.clearButton:GetScript('OnClick')()
            assert(card.rows[1].total:GetText():find('—'))
            skills={{skillID=186,name='Mining',rank=125,maxRank=225}}; ns.Refresh()
            assert(not card:IsShown())''')

    def test_cost_tooltip_is_short_structured_and_deduplicates_missing_prices(self):
        self.check('''AuctionPriceLite={GetItemPrice=function(id)
                if id~=3371 then return 100,200 end end}
            ns.Command('show'); ns.SetTarget(5); ns.Render()
            local card=ns.costCards[1]
            local lines,rows={},{}
            local clears=0
            GameTooltip={SetOwner=function() end,ClearLines=function() clears=clears+1; lines={}; rows={} end,
                AddLine=function(_,value) lines[#lines+1]=value end,
                AddDoubleLine=function(_,label,value) rows[#rows+1]={label,value} end,
                Show=function() tooltipShown=true end,Hide=function() tooltipShown=false end}
            card:GetScript('OnEnter')(card)
            assert(clears==1 and tooltipShown and lines[1]=='Pricing details')
            assert(#rows==3 and rows[1][2]=='AuctionPriceLite' and rows[2][2]=='Selected step')
            assert(#card.missingPrices==1 and card.missingPrices[1]=='Empty Vial')
            local body=table.concat(lines,' ')
            assert(body:find('Empty Vial') and not body:find('per craft; about') and #body<160)
            card:GetScript('OnLeave')(card); assert(not tooltipShown)
            card:GetScript('OnEnter')(card); assert(clears==2 and #rows==3)''')

    def test_no_target_no_plan_or_export(self):
        self.check('''assert(ns.plan==nil and next(ns.db.targets)==nil)
            assert(not ns.frame:IsShown()); ns.Command('show'); assert(ns.frame:IsShown())
            assert(ns.plan==nil and ns.exportButton.enabled==false)''')

    def test_valid_targets_and_partial_materials(self):
        self.check('''assert(not ns.SetTarget('0')); assert(not ns.SetTarget('301'))
            assert(not ns.SetTarget('2.5')); assert(not ns.SetTarget('nan'))
            assert(ns.SetTarget('5')); ns.Render(); local p=ns.plan
            assert(#p.steps==1 and p.steps[1].recipes[1].crafts==4)
            assert(#p.materials==2)
            for _,m in ipairs(p.materials) do assert(m.quantity==4) end''')

    def test_skill_changes_never_export(self):
        self.install_farming_tool_spy()
        self.check('''ns.SetTarget(55); ns.Render(); assert(#batches==0)
            skills[1].rank=20; Fire('SKILL_LINES_CHANGED'); Tick()
            assert(ns.plan.rank==20 and #batches==0)
            Fire('PLAYER_LEVEL_UP'); Tick(); assert(#batches==0)''')

    def test_opt_in_export_preserves_and_is_repeatable(self):
        self.install_farming_tool_spy()
        self.check('''goals={[2447]=999,[123]=7}
            ns.SetTarget(10); ns.Render(); assert(#batches==0 and ns.exportButton.enabled)
            ns.exportButton:GetScript('OnClick')(); assert(#batches==1)
            assert(batches[1].showTracker and #batches[1].materials==#ns.plan.materials)
            assert(goals[2447]==999 and goals[123]==7 and goals[3371]==9)
            assert(ns.Export(ns.plan)); assert(#batches==2 and goals[3371]==9)
        ''')

    def test_provider_failure_preserves_export_history(self):
        self.install_farming_tool_spy()
        self.check('''ns.db.exports.alchemy={[765]=99}
            rejectBatch='Provider capacity reached'
            ns.SetTarget(10); ns.Render()
            ns.exportButton:GetScript('OnClick')()
            assert(#batches==1 and next(goals)==nil)
            assert(ns.db.exports.alchemy[765]==99 and next(ns.db.exports.alchemy,765)==nil)
            assert(ns.statusText:GetText()==rejectBatch)''')

    def test_no_optional_addon(self):
        self.check("ns.SetTarget(75); ns.Render(); assert(ns.plan); assert(not ns.CanExport()); assert(not ns.Export(ns.plan))")

    def test_older_provider_prompts_update_without_disabling_planning(self):
        self.check('''C_AddOns={IsAddOnLoaded=function(name) return name=='ItemFarmingTool' end}
            ItemFarmingToolDB={items={}}
            SlashCmdList.ITEMFARMINGTOOL=function() error('Player command must not be called') end
            ns.SetTarget(10); ns.Render()
            assert(ns.plan and not ns.exportButton.enabled)
            assert(ns.statusText:GetText():find('Update ItemFarmingTool'))
            local ok,reason=ns.Export(ns.plan)
            assert(not ok and reason:find('Update ItemFarmingTool'))
            assert(#ItemFarmingToolDB.items==0 and next(ns.db.exports)==nil)''')

    def test_intermediate_oils_not_double_counted(self):
        self.check('''skills[1].rank=130; ns.Refresh(); local p=ns.Plan('alchemy',ns.player,165)
            local mats={}; for _,m in ipairs(p.materials) do mats[m.name]=m.quantity end
            assert(mats['Fire Oil']==nil and mats['Firefin Snapper']==40 and mats['Kingsblood']==15)
            skills[1].rank=150; ns.Refresh(); p=ns.Plan('alchemy',ns.player,165)
            mats={}; for _,m in ipairs(p.materials) do mats[m.name]=m.quantity end
            assert(mats['Firefin Snapper']==30 and mats['Empty Vial']==15)
            owned={[6371]=10}; p=ns.Plan('alchemy',ns.player,165)
            mats={}; for _,m in ipairs(p.materials) do mats[m.name]=m.quantity end
            assert(mats['Firefin Snapper']==20)
        ''')

    def test_tailoring_bolts_and_refreshed_full_source_route(self):
        self.check('''skills={{skillID=197,name='Tailoring',rank=1,maxRank=75}}; ns.Refresh()
            local p=ns.Plan('tailoring',ns.player,55); local mats={}
            for _,m in ipairs(p.materials) do mats[m.name]=m.quantity end
            assert(mats['Linen Cloth']==60 and mats['Bolt of Linen Cloth']==nil)
            skills[1].rank=225; ns.Refresh(); p=ns.Plan('tailoring',ns.player,300)
            mats={}; for _,m in ipairs(p.materials) do mats[m.name]=m.quantity end
            assert(mats['Runecloth']==3585 and mats['Rugged Leather']==276)
            assert(mats['Ironweb Spider Silk']==155)
            assert(p.steps[#p.steps].to==300 and ns.Guides.tailoring.cap==300)
            assert(table.concat(p.warnings):find('world%-drop'))''')

    def test_sparse_modern_profession_slots(self):
        self.check('''C_SkillInfo=nil
            GetProfessions=function() return nil,nil,nil,4,5,6 end
            GetProfessionInfo=function(i) return 'Localized',nil,25,75,nil,nil,({[4]=356,[5]=185,[6]=129})[i] end
            ns.Refresh(); assert(ns.player.professions.fishing and ns.player.professions.cooking)
            assert(ns.player.professions['first-aid'])''')

    def test_legacy_skills_and_collapse_warning(self):
        self.check('''C_SkillInfo=nil; GetNumSkillLines=function() return 2 end
            GetSkillLineInfo=function(i)
                if i==1 then return 'Professions',true,true end
                return 'Engineering',false,false,55,0,0,75
            end
            ns.Refresh(); assert(ns.player.professions.engineering.rank==55 and ns.player.collapsed)''')

    def test_unlearn_drops_live_plan(self):
        self.check('''ns.SetTarget(100); ns.Render(); assert(ns.plan)
            skills={}; Fire('SKILL_LINES_CHANGED'); Tick()
            assert(ns.plan==nil and ns.db.selected==nil)''')

    def test_character_level_and_lockpicking_caps(self):
        self.check('''ns.SetTarget(300); ns.Render(); local found=false
            for _,w in ipairs(ns.plan.warnings) do if w:find('too low') then found=true end end
            assert(found)
            skills={{skillID=633,name='Lockpicking',rank=1,maxRank=100}}; ns.Refresh()
            local p=ns.Plan('lockpicking',ns.player,150); assert(#p.materials==0)
            local text=table.concat(p.warnings); assert(text:find('30') and text:find('100'))''')

    def test_targets_persist_per_profession(self):
        self.check('''ns.SetTarget(100)
            skills[2]={skillID=197,name='Tailoring',rank=1,maxRank=75}; ns.Refresh()
            ns.Command('select tailoring'); ns.SetTarget(55); ns.Command('select alchemy')
            assert(ns.plan.target==100 and ns.db.targets.tailoring==55)''')

    def test_ui_apply_clear_and_export_clicks(self):
        self.check('''ns.Command('show'); ns.targetInput:SetText('55')
            ns.targetInput:GetScript('OnEnterPressed')(); assert(ns.plan.target==55)
            ns.frame:GetScript('OnDragStop')(ns.frame)
            ns.Command('reset'); assert(ns.db.position==nil)''')

    def test_all_route_invariants_and_plans(self):
        self.check('''for slug,g in pairs(ns.Guides) do
            local expected=1
            for _,s in ipairs(g.steps) do
                assert(s.from==expected and s.to>s.from,slug); expected=s.to
                for _,r in ipairs(s.recipes or {}) do
                    assert(r.crafts>0)
                    for _,m in ipairs(r.materials) do assert(ns.ItemIDs[m.name] and m.quantity>0 and m.quantity%1==0,m.name) end
                end
            end
            assert(expected==g.cap,slug)
            for _,rank in ipairs({1,74,75,149,150,224,225,264,265,299,300}) do
                local player={level=60,faction='Alliance',professions={[slug]={rank=rank,cap=300}}}
                local p=assert(ns.Plan(slug,player,300))
                for _,m in ipairs(p.materials) do assert(m.id and m.quantity>0 and m.quantity%1==0) end
            end
        end''')

    def test_quest_materials_and_known_recipe_detection(self):
        self.check('''skills={{skillID=164,name='Blacksmithing',rank=240,maxRank=300}}; ns.Refresh()
            local p=ns.Plan('blacksmithing',ns.player,245); local bars
            for _,m in ipairs(p.materials) do if m.name=='Thorium Bar' then bars=m.quantity end end
            assert(bars==130)
            IsPlayerSpell=function() return true end
            p=ns.Plan('blacksmithing',ns.player,245)
            for _,m in ipairs(p.materials) do if m.name=='Thorium Bar' then assert(m.quantity==110) end end
            skills={{skillID=185,name='Cooking',rank=225,maxRank=225}}; ns.Refresh()
            p=ns.Plan('cooking',ns.player,226); local mats={}
            for _,m in ipairs(p.materials) do mats[m.name]=m.quantity end
            assert(mats['Giant Egg']==12 and mats['Zesty Clam Meat']==10 and mats['Alterac Swiss']==20)''')

    def test_corrupt_settings_are_sanitized(self):
        self.check('''ProfessionGuideDB={targets={alchemy=-1,tailoring=55,invalid=300},selected='invalid',
                position={point='BAD',x=0,y=0},hidden='bad'}
            ns.db=nil; ns.LoadSettings(); assert(ns.db.targets.tailoring==55)
            assert(ns.db.targets.alchemy==nil and ns.db.targets.invalid==nil)
            assert(ns.db.position==nil and ns.db.selected==nil and ns.db.hidden==true)''')

    def test_actual_itemfarmingtool_integration(self):
        self.start_paired_session()
        self.check('''SlashCmdList.ITEMFARMINGTOOL=function() error('Player command must not be called') end
            assert(ift.AddItem('2447',100)); assert(ift.AddItem('2589',7))
            ift.Command('hide')
            ns.SetTarget(10); ns.Render(); assert(ns.Export(ns.plan))
            assert(ift.Find(2447).goal==100 and ift.Find(2589).goal==7)
            assert(ift.frame:IsShown())
            assert(ift.Find(3371).goal==9); local total=#ift.db.items
            assert(ns.Export(ns.plan)); assert(#ift.db.items==total)
            ns.plan.materials[#ns.plan.materials+1]={quantity=1}
            assert(not ns.Export(ns.plan))
            assert(#ift.db.items==total and ift.Find(2447).goal==100)''')

    def test_workshop_recipe_selection_keeps_full_route_totals(self):
        self.check('''skills[1].rank=65; ns.Refresh(); ns.SetTarget(120); ns.Render()
            assert(#ns.route==2 and ns.recipeText:GetText()=='Elixir of Minor Fortitude')
            local count=#ns.plan.materials
            ns.routeButtons[2]:GetScript('OnClick')(ns.routeButtons[2])
            assert(ns.recipeText:GetText()=='Elixir of Wisdom')
            assert(ns.detailText:GetText():find('30 crafts'))
            assert(#ns.plan.materials==count and ns.shoppingTitle:GetText():find('120'))
            assert(ns.detailText:GetText():find('2 Briarthorn'))
            Fire('BAG_UPDATE_DELAYED'); Tick()
            assert(ns.recipeText:GetText()=='Elixir of Wisdom')''')

    def test_workshop_advance_and_target_reset(self):
        self.check('''skills[1].rank=65; ns.Refresh(); ns.SetTarget(120); ns.Render()
            skills[1].rank=90; Fire('SKILL_LINES_CHANGED'); Tick()
            assert(ns.selectedStep.from==90 and ns.recipeText:GetText()=='Elixir of Wisdom')
            ns.SetTarget(150); ns.Render(); ns.routeButtons[3]:GetScript('OnClick')(ns.routeButtons[3])
            assert(ns.recipeText:GetText()=='Fire Oil')
            ns.SetTarget(120); ns.Render(); assert(ns.recipeText:GetText()=='Elixir of Wisdom')
            assert(not ns.routeButtons[3]:IsShown())''')

    def test_workshop_notes_and_clear_target(self):
        self.check('''ns.Command('show'); ns.SetTarget(120); ns.Render()
            ns.notesButton:GetScript('OnClick')()
            assert(ns.showNotes and ns.notesText:IsShown() and not ns.recipeText:IsShown())
            assert(ns.trainingRows[1].label:GetText():find('Ainethil'))
            ns.notesButton:GetScript('OnClick')()
            assert(not ns.showNotes and ns.recipeText:IsShown())
            ns.clearButton:GetScript('OnClick')()
            assert(ns.plan==nil and not ns.exportButton.enabled)
            assert(ns.materialMessage:GetText():find('Choose a target'))
            assert(not ns.materialRows[1]:IsShown())''')

    def test_workshop_material_columns_and_async_icons(self):
        self.check('''ns.Command('show'); ns.SetTarget(10); ns.Render()
            owned={[3371]=20}; ns.Refresh()
            for i,m in ipairs(ns.plan.materials) do
                local row=ns.materialRows[i]
                assert(row.need:GetText()==tostring(m.quantity))
                if m.id==3371 then
                    assert(row.have:GetText()=='20' and row.short:GetText():find('0'))
                    itemData[3371]={name='Empty Vial',icon=987}
                    Fire('GET_ITEM_INFO_RECEIVED',3371); Tick()
                    assert(row.icon.texture==987)
                    row:GetScript('OnEnter')(row); row:GetScript('OnLeave')()
                end
            end''')

    def test_workshop_both_engineering_recipes_and_gathering(self):
        self.check('''ns.Command('show')
            skills={{skillID=202,name='Engineering',rank=135,maxRank=150}}; ns.Refresh()
            ns.SetTarget(150); ns.Render()
            assert(ns.recipeText:GetText():find('Heavy Blasting Powder'))
            assert(ns.recipeText:GetText():find('Whirring Bronze Gizmo'))
            assert(ns.costCards[1].title:GetText()=='Heavy Blasting Powder')
            assert(ns.costCards[2].title:GetText()=='Whirring Bronze Gizmo')
            skills={{skillID=186,name='Mining',rank=125,maxRank=150}}; ns.Refresh()
            ns.SetTarget(175); ns.Render()
            assert(ns.recipeText:GetText()=='Gathering route')
            assert(not ns.costCards[1]:IsShown() and not ns.costCards[2]:IsShown())
            assert(ns.detailText:GetText():find('Thousand Needles'))
            assert(#ns.plan.materials==0 and not ns.exportButton.enabled)''')

    def test_workshop_complete_and_source_end_states(self):
        self.check('''ns.Command('show'); ns.SetTarget(1); ns.Render()
            assert(ns.recipeText:GetText()=='Target reached' and #ns.route==0)
            skills={{skillID=197,name='Tailoring',rank=265,maxRank=300}}; ns.Refresh()
            ns.Guides.tailoring.cap=265
            local limited={}
            for _,s in ipairs(ns.Guides.tailoring.steps) do
                if s.from<265 then s.to=math.min(s.to,265); limited[#limited+1]=s end
            end
            ns.Guides.tailoring.steps=limited
            ns.SetTarget(300); ns.Render()
            assert(ns.recipeText:GetText()=='No further source steps')
            assert(ns.warningText:GetText():find('265') and not ns.exportButton.enabled)''')

    def test_blizzard_spell_icons_modern_legacy_and_bundled_paths(self):
        self.check('''C_Spell={GetSpellTexture=function() return 12345 end}
            assert(ns.SpellIcon(2334)==12345)
            C_Spell=nil; GetSpellTexture=function() return 54321 end
            assert(ns.SpellIcon(2334)==54321)
            GetSpellTexture=nil; GetSpellInfo=function() return 'Recipe',nil,45678 end
            assert(ns.SpellIcon(2334)==45678)
            GetSpellInfo=nil; assert(ns.SpellIcon(2334)==ns.RecipeIcons[2334])
            for slug,g in pairs(ns.Guides) do
                assert(ns.ProfessionIcon(slug):find('Interface'))
                for _,s in ipairs(g.steps) do
                    assert(ns.StepIcon(slug,s))
                    for _,r in ipairs(s.recipes or {}) do assert(ns.RecipeIcons[r.spell],r.name) end
                end
            end''')

    def test_profession_api_icon_survives_skill_line_merge(self):
        self.check('''GetProfessions=function() return 1 end
            GetProfessionInfo=function() return 'Alchemy',98765,1,75,nil,nil,171 end
            ns.Refresh(); assert(ns.player.professions.alchemy.icon==98765)
            assert(ns.ProfessionIcon('alchemy')==98765)
            assert(ns.profButton:GetText():find('98765'))''')

    def test_uncached_item_icon_apis_and_failed_lookup_fallbacks(self):
        self.check('''C_Item.GetItemIconByID=function() return 1234 end
            assert(ns.ItemIcon(3371)==1234)
            C_Item.GetItemIconByID=function() error('Unsupported') end
            GetItemIcon=function() return 5678 end; assert(ns.ItemIcon(3371)==5678)
            GetItemIcon=nil; C_Item.GetItemIconByID=nil
            C_Item.GetItemInfoInstant=function() return 3371,'Misc','Other','',9876 end
            assert(ns.ItemIcon(3371)==9876)
            C_Item.GetItemInfoInstant=nil
            local requests=0; C_Item.RequestLoadItemDataByID=function() requests=requests+1 end
            assert(ns.ItemIcon(999999)==nil); assert(ns.ItemIcon(999999)==nil)
            assert(requests==1)
            itemData[999999]={name='New item',icon=4567}; assert(ns.ItemIcon(999999)==4567)
            assert(ns.ValidIcon(0)==nil and ns.ValidIcon('')==nil and ns.ValidIcon({})==nil)''')

    def test_workshop_icons_follow_recipe_and_profession(self):
        self.check('''skills[1].rank=65; ns.Refresh(); ns.SetTarget(120); ns.Render()
            assert(ns.recipeIcon.texture==ns.RecipeIcons[2334])
            assert(ns.routeButtons[1].icon.texture==ns.recipeIcon.texture)
            ns.routeButtons[2]:GetScript('OnClick')(ns.routeButtons[2])
            assert(ns.recipeIcon.texture==ns.RecipeIcons[3171])
            C_Item.GetItemIconByID=function(id) return id+100000 end
            ns.Render(); assert(ns.detailText:GetText():find('|T'))
            for i,m in ipairs(ns.plan.materials) do assert(ns.materialRows[i].icon.texture==m.id+100000) end
            skills={{skillID=186,name='Mining',rank=1,maxRank=75}}; ns.Refresh()
            assert(ns.recipeIcon.texture==ns.ProfessionIcon('mining'))
            assert(not tostring(ns.recipeIcon.texture):find('QuestionMark'))''')

    def test_recipe_art_overrides_valid_placeholder_spell_texture(self):
        self.check('''C_Spell={GetSpellTexture=function() return 999999 end}
            skills[1].rank=64; ns.Refresh(); ns.SetTarget(120); ns.Render()
            assert(ns.recipeIcon.texture=='Interface\\\\Icons\\\\inv_potion_70')
            assert(ns.routeButtons[1].icon.texture==ns.RecipeIcons[2331])
            assert(ns.routeButtons[2].icon.texture==ns.RecipeIcons[2334])
            ns.routeButtons[3]:GetScript('OnClick')(ns.routeButtons[3])
            assert(ns.recipeIcon.texture==ns.RecipeIcons[3171])
            assert(ns.ProfessionIcon('alchemy')==999999)
            assert(ns.RecipeIcon(987654321)==999999) -- unmapped recipes still use APIs
        ''')

    def create_minimap(self):
        self.check('''Minimap=CreateFrame('Frame',nil,UIParent); Minimap:SetSize(140,140)
            Minimap.centerX,Minimap.centerY=100,100
            GetCursorPosition=function() return cursorX or 200,cursorY or 100 end
            ns.InitMinimapButton()''')

    def test_minimap_toggle_never_exports_and_init_is_idempotent(self):
        self.create_minimap()
        self.install_farming_tool_spy()
        self.check('''assert(ns.minimapButton:IsShown() and ns.db.hidden)
            ns.SetTarget(120)
            ns.minimapButton:GetScript('OnClick')(); assert(ns.frame:IsShown())
            ns.minimapButton:GetScript('OnClick')(); assert(not ns.frame:IsShown())
            local count=#frames; ns.InitMinimapButton(); assert(#frames==count)
            assert(#batches==0 and ns.minimapButton:GetScript('OnUpdate')==nil)
            ns.minimapButton:GetScript('OnEnter')(ns.minimapButton)
            ns.minimapButton:GetScript('OnLeave')()''')

    def test_minimap_drag_scale_and_cleanup(self):
        self.create_minimap()
        self.check('''local b=ns.minimapButton
            Minimap.scale=2; cursorX,cursorY=200,400
            b:GetScript('OnDragStart')(b); assert(b:GetScript('OnUpdate'))
            b:GetScript('OnUpdate')(); assert(math.abs(ns.db.minimapAngle-90)<0.001)
            assert(math.abs(b.point[4])<0.001 and math.abs(b.point[5]-78)<0.001)
            b:GetScript('OnDragStop')(b); assert(b:GetScript('OnUpdate')==nil)
            local angle=ns.db.minimapAngle; b:GetScript('OnDragStart')(b)
            Minimap.scale=0; b:GetScript('OnUpdate')(); assert(ns.db.minimapAngle==angle)
            ns.Command('minimap hide'); assert(b:GetScript('OnUpdate')==nil and not b:IsShown())''')

    def test_minimap_visibility_commands_and_saved_settings(self):
        self.create_minimap()
        self.check('''ns.Command('minimap hide'); assert(ns.db.minimapButton==false)
            ns.db=nil; ns.LoadSettings(); ns.UpdateMinimapButton()
            assert(not ns.minimapButton:IsShown())
            ns.Command('minimap show'); assert(ns.minimapButton:IsShown())
            ns.db.minimapAngle=15; ns.Command('minimap reset')
            assert(ns.db.minimapAngle==140 and ns.db.minimapButton)
            ns.Command('minimap'); assert(not ns.minimapButton:IsShown())
            ns.Command('minimap invalid'); assert(not ns.minimapButton:IsShown())
            ns.db.minimapAngle=0/0; ns.db=nil; ns.LoadSettings(); assert(ns.db.minimapAngle==140)''')

    def test_minimap_resize_and_square_shape(self):
        self.create_minimap()
        self.check('''ns.db.minimapAngle=45; GetMinimapShape=function() return 'SQUARE' end
            Minimap:SetSize(200,200); Minimap:GetScript('OnSizeChanged')(Minimap)
            assert(math.abs(ns.minimapButton.point[4]-108)<0.001)
            assert(math.abs(ns.minimapButton.point[5]-108)<0.001)
            GetMinimapShape=nil; ns.PositionMinimapButton()
            assert(ns.minimapButton.point[4]<108)''')

    def test_linked_alchemy_choice_updates_both_steps_and_materials(self):
        self.check('''skills[1].rank=250; ns.Refresh(); ns.SetTarget(300); ns.Render()
            assert(ns.SetChoice('alchemy','finish','mana')); ns.Render()
            assert(#ns.plan.steps==2)
            assert(ns.plan.steps[1].recipes[1].name=='Elixir of Greater Intellect')
            assert(ns.plan.steps[2].recipes[1].name=='Superior Mana Potion')
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats.Blindweed==131 and mats.Sungrass==110 and mats['Crystal Vial']==76)
            assert(mats['Stonescale Eel']==nil and mats['Leaded Vial']==nil)
            assert(ns.choiceDelta:find('Reduces 47 Stonescale Eel'))
            ns.db=nil; ns.LoadSettings(); assert(ns.ActiveChoices('alchemy')['finish']=='mana')
            assert(ns.SetChoice('alchemy','finish','default')); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Stonescale Oil')''')

    def test_alternate_dropdown_comparison_and_no_target(self):
        self.check('''ns.Command('show'); skills[1].rank=250; ns.Refresh()
            assert(ns.optionButton:IsShown() and ns.plan==nil)
            ns.optionButton:GetScript('OnClick')(); assert(ns.alternateMenu:IsShown())
            local alternate=ns.alternateMenu.buttons[2]
            alternate:GetScript('OnClick')(alternate)
            assert(not ns.alternateMenu:IsShown() and ns.plan==nil)
            assert(ns.recipeText:GetText()=='Elixir of Greater Intellect')
            assert(not ns.exportButton.enabled)
            ns.SetTarget(300); ns.Render(); ns.compareButton:GetScript('OnClick')()
            assert(ns.compareText:IsShown() and ns.compareText:GetText():find('Stonescale Eel'))
            assert(ns.ActiveChoices('alchemy')['finish']=='mana')
            ns.compareButton:GetScript('OnClick')(); assert(not ns.compareText:IsShown())''')

    def test_enchanting_consistent_paths_and_minimum_estimate(self):
        self.check('''skills={{skillID=333,name='Enchanting',rank=20,maxRank=150}}; ns.Refresh()
            ns.SetTarget(150); ns.Render()
            local defaults=ns.GetGuideSteps('enchanting')
            assert(defaults[4].recipes[1].name=='Enchant Chest - Inferior Stamina')
            assert(ns.SetChoice('enchanting','early-path','essence')); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Enchant Bracer - Minor Deflect')
            assert(ns.plan.steps[#ns.plan.steps].recipes[1].name=='Enchant 2H Weapon - Lesser Intellect')
            ns.SetChoice('enchanting','early-path','essence-trainer'); ns.Render()
            assert(ns.plan.steps[#ns.plan.steps].recipes[1].name=='Enchant Boots - Minor Stamina')
            skills[1].rank=250; ns.Refresh(); ns.SetTarget(265)
            ns.SetChoice('enchanting','lotus','strength'); ns.Render()
            assert(ns.detailText:GetText():find('At least 15 crafts'))
            assert(ns.warningText:GetText():find('Minimum craft count'))''')

    def test_refreshed_leatherworking_choices_compose(self):
        self.check('''skills={{skillID=165,name='Leatherworking',rank=235,maxRank=300}}; ns.Refresh()
            ns.SetTarget(300); ns.SetChoice('leatherworking','shoes','shoes')
            ns.SetChoice('leatherworking','finish','bracers'); ns.Render()
            local names={}; for _,s in ipairs(ns.plan.steps) do names[s.from]=s.recipes[1].name end
            assert(names[235]=='Blue Suede Shoes' and names[265]=='Runic Leather Headband')
            assert(names[275]=='Blue Suede Bracers')
            assert(not ns.SetChoice('leatherworking','heavy-hides','leather'))''')

    def test_choice_requirements_faction_and_corrupt_saves(self):
        self.check('''skills={{skillID=197,name='Tailoring',rank=215,maxRank=225}}; ns.Refresh()
            ns.SetTarget(225); assert(ns.SetChoice('tailoring','bags','belts')); ns.Render()
            assert(ns.warningText:GetText():find('level 35'))
            assert(not ns.SetChoice('alchemy','invalid','invalid'))
            local group,option=ns.FindChoice('blacksmithing','bronze','warhammer')
            option.faction='Horde'
            assert(not ns.SetChoice('blacksmithing',group.id,option.id))
            ns.db.choices.invalid={bad='bad'}; ns.db.choices.alchemy={['finish']='mana',bad='bad'}
            ns.db.exports={alchemy={['bad']='bad',[2447]=-1,[3371]=42}}
            ns.db=nil; ns.LoadSettings()
            assert(ns.db.choices.invalid==nil and ns.db.choices.alchemy.bad==nil)
            assert(ns.db.choices.alchemy['finish']=='mana' and ns.db.exports.alchemy[3371]==42)
            assert(ns.db.exports.alchemy[2447]==nil)''')

    def test_comparisons_and_choices_do_not_write_farming_goals(self):
        self.install_farming_tool_spy()
        self.check('''skills[1].rank=250; ns.Refresh(); ns.SetTarget(300); ns.Render()
            local group=ns.GroupForStep('alchemy',ns.selectedStep)
            local comparison=ns.CompareChoice('alchemy',group,group.options[2])
            assert(comparison:find('Adds 121 Blindweed') and ns.ActiveChoices('alchemy')['finish']==nil)
            ns.SetChoice('alchemy','finish','mana'); ns.Render()
            Fire('BAG_UPDATE_DELAYED'); Fire('SKILL_LINES_CHANGED'); Tick()
            assert(#batches==0 and next(ns.db.exports)==nil)''')

    def test_previous_export_review_survives_reexport(self):
        self.start_paired_session()
        self.check('''skills[1].rank=250; ns.Refresh(); ns.SetTarget(300); ns.Render()
            assert(ns.Export(ns.plan)); assert(ift.Find(13422).goal==47)
            ns.SetChoice('alchemy','finish','mana'); ns.Render()
            local review=ns.ExportReview(ns.plan)
            assert(review:find('Stonescale Eel') and review:find('needs 0'))
            assert(ift.Find(13422).goal==47)
            assert(ns.Export(ns.plan)); assert(ns.ExportReview(ns.plan):find('Stonescale Eel'))
            ift.RemoveItem(13422); assert(not ns.ExportReview(ns.plan):find('Stonescale Eel'))
            assert(ift.Find(8838).goal==110)''')

    def test_all_alternate_paths_have_valid_coverage_items_and_icons(self):
        self.check('''for slug,groups in pairs(ns.Alternates) do
            local player={level=60,faction='Alliance',professions={[slug]={rank=1,cap=300}}}
            local function validate(choices)
                local expected=1
                for _,s in ipairs(ns.GetGuideSteps(slug,choices)) do
                    assert(s.from==expected and s.to>s.from,slug..':'..expected); expected=s.to
                    for _,r in ipairs(s.recipes) do
                        assert(ns.RecipeIcons[r.spell],r.name)
                        for _,m in ipairs(r.materials) do assert(ns.ItemIDs[m.name] and m.quantity%1==0 and m.quantity>0,m.name) end
                    end
                end
                assert(expected==ns.Guides[slug].cap,slug)
                for _,rank in ipairs({1,74,109,130,149,165,215,240,264,295}) do
                    player.professions[slug].rank=rank
                    local plan=assert(ns.Plan(slug,player,300,choices))
                    for _,m in ipairs(plan.materials) do assert(m.id and m.quantity>0 and m.quantity%1==0) end
                end
            end
            local mixed={}
            for _,g in ipairs(groups) do
                for _,o in ipairs(g.options) do validate({[g.id]=o.id}) end
                mixed[g.id]=g.options[#g.options].id
            end
            validate(mixed)
        end''')

    def test_minimum_comparison_warning_and_numeric_save_normalization(self):
        self.check('''skills={{skillID=197,name='Tailoring',rank=215,maxRank=225}}; ns.Refresh()
            ns.SetTarget(225); ns.SetChoice('tailoring','bags','belts'); ns.Render()
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats.Runecloth==150 and mats['Rune Thread']==10)
            assert(mats['Mageweave Cloth']==nil)
            skills={{skillID=333,name='Enchanting',rank=250,maxRank=300}}; ns.Refresh()
            ns.SetTarget(265); ns.Render(); ns.SetChoice('enchanting','lotus','strength'); ns.Render()
            assert(ns.plan.minimum and ns.shoppingTitle:GetText():find('minimum'))
            assert(ns.choiceDelta:find('minimum estimates'))
            ns.db.targets.alchemy='90'; ns.db.exports.alchemy={['3371']='42'}
            ns.db=nil; ns.LoadSettings()
            assert(ns.db.targets.alchemy==90 and ns.db.exports.alchemy[3371]==42)''')

    def test_prepared_heavy_hides_follow_refreshed_route_and_refresh(self):
        self.check('''ns.Command('show')
            skills={{skillID=165,name='Leatherworking',rank=164,maxRank=225}}
            owned={[4236]=6,[4235]=11,[4234]=68,[2321]=2}
            ns.Refresh(); ns.SetTarget(195); ns.Render()
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Heavy Hide']==5 and mats.Salt==15 and mats['Heavy Leather']==188)
            assert(mats['Thick Leather']==55)
            local cured=ns.plan.prepared[1]
            assert(cured.name=='Cured Heavy Hide' and cured.used==6 and cured.missing==5)
            assert(ns.preparedText:IsShown() and ns.preparedText:GetText():find('use 6 from bags'))
            owned[4236]=37; Fire('BAG_UPDATE_DELAYED'); Tick()
            mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Heavy Hide']==nil and mats.Salt==nil)
            assert(ns.plan.prepared[1].used==11 and ns.plan.prepared[1].missing==0)
            assert(ns.preparedText:GetText():find('still need 0'))
            ns.clearButton:GetScript('OnClick')(); assert(not ns.preparedText:IsShown())''')

    def test_raw_and_cured_hides_are_distinct_and_bank_is_not_credited(self):
        self.check('''skills={{skillID=165,name='Leatherworking',rank=164,maxRank=225}}
            owned={[4235]=100}; ns.Refresh(); ns.SetTarget(195); ns.Render()
            assert(ns.plan.prepared[1].used==0 and ns.plan.prepared[1].missing==11)
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m end
            assert(mats['Heavy Hide'].quantity==11 and mats['Heavy Hide'].owned==100)
            assert(mats.Salt.quantity==33)
            bankQueries=0
            C_Item.GetItemCount=function(id,includeBank)
                if includeBank then bankQueries=bankQueries+1; return 999 end
                return owned[id] or 0
            end
            ns.Refresh(); assert(ns.plan.prepared[1].used==0 and bankQueries==0)''')

    def test_prepared_credit_does_not_skip_leveling_crafts(self):
        self.check('''skills={{skillID=197,name='Tailoring',rank=1,maxRank=75}}
            owned={[2996]=100}; ns.Refresh(); ns.SetTarget(55); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Bolt of Linen Cloth')
            assert(ns.plan.steps[1].recipes[1].crafts==30)
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Linen Cloth']==60) -- these crafts are needed for skill points
            assert(#ns.plan.prepared==0) -- route output already covers all 28 belts
            skills={{skillID=197,name='Tailoring',rank=30,maxRank=75}}; ns.Refresh()
            ns.SetTarget(55); ns.Render()
            assert(ns.plan.prepared[1].used==28 and ns.plan.prepared[1].missing==0)
            mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Linen Cloth']==nil)''')

    def test_current_source_routes_and_oil_yield(self):
        self.check('''assert(ns.SourceDate=='2026-11-23')
            skills={{skillID=171,name='Alchemy',rank=250,maxRank=300}}; ns.Refresh()
            ns.SetTarget(300); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Stonescale Oil')
            assert(ns.plan.steps[1].recipes[1].crafts==47)
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Stonescale Eel']==47 and mats['Leaded Vial']==47 and mats['Stonescale Oil']==nil)
            assert(mats.Blindweed==10 and mats['Crystal Vial']==54)
            ns.SetChoice('alchemy','finish','mana'); ns.Render()
            mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Stonescale Eel']==nil and mats['Leaded Vial']==nil)
            assert(mats.Blindweed==131 and mats.Sungrass==110 and mats['Crystal Vial']==76)
            assert(ns.plan.steps[1].from==250 and ns.plan.steps[1].to==265)''')

    def test_refreshed_cooking_enchanting_and_pattern_requirements(self):
        self.check('''skills={{skillID=185,name='Cooking',rank=225,maxRank=300}}; ns.Refresh()
            ns.SetTarget(300); ns.Render()
            assert(#ns.plan.steps==2 and ns.plan.steps[1].recipes[1].crafts==72)
            assert(ns.plan.steps[2].from==285 and ns.plan.steps[2].recipes[1].name=='Nightfin Soup'
                and ns.plan.steps[2].recipes[1].crafts==18)
            skills={{skillID=333,name='Enchanting',rank=265,maxRank=300}}; ns.Refresh()
            ns.SetTarget(300); ns.Render()
            assert(ns.plan.steps[3].from==275 and ns.plan.steps[3].recipes[1].name=='Wizard Oil'
                and ns.plan.steps[3].recipes[1].crafts==26)
            assert(ns.plan.steps[#ns.plan.steps].recipes[1].name=='Runed Arcanite Rod')
            skills={{skillID=197,name='Tailoring',rank=280,maxRank=300}}; ns.Refresh()
            ns.SetTarget(300); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Runecloth Shoulders')
            assert(ns.plan.steps[1].recipes[1].crafts==58)
            assert(ns.warningText:GetText():find('rare') or ns.warningText:GetText():find('world%-drop'))
            skills={{skillID=129,name='First Aid',rank=275,maxRank=300}}; ns.Refresh()
            ns.SetTarget(300); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Runecloth Bandage')
            assert(ns.SetChoice('first-aid','artisan','potions')); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Major Healing Potion')
            assert(ns.warningText:GetText():find('Pexmit'))''')

    def test_blacksmithing_125_routes_plan_the_correct_materials(self):
        self.check('''skills={{skillID=164,name='Blacksmithing',rank=125,maxRank=150}}; ns.Refresh()
            local function plan(choice)
                local result=ns.Plan('blacksmithing',ns.player,140,{bronze=choice})
                local materials={}
                for _,item in ipairs(result.materials) do materials[item.name]=item.quantity end
                return result.steps[1].recipes[1],materials
            end
            local recipe,materials=plan('default')
            assert(recipe.name=='Silvered Bronze Gauntlets' and recipe.crafts==15)
            assert(materials['Bronze Bar']==120 and materials['Silver Bar']==15 and materials['Coarse Stone']==60)
            recipe,materials=plan('warhammer')
            assert(recipe.name=='Bronze Warhammer' and recipe.crafts==15)
            assert(materials['Bronze Bar']==120 and materials['Strong Flux']==15 and materials['Medium Leather']==15)
            assert(materials['Coarse Stone']==nil and materials['Silver Bar']==nil)''')

    def test_source_refresh_retires_only_removed_saved_choices(self):
        self.check('''ns.db.choices={leatherworking={['heavy-hides']='leather'},
                blacksmithing={imperial='ebon',bronze='bracers'},alchemy={['finish']='mana'}}
            ns.db.sourceDate='2026-11-12'; ns.db.targets.alchemy=300
            ns.db.exports.alchemy={[3371]=42}; ns.db=nil; ns.LoadSettings()
            assert(ns.db.choices.leatherworking['heavy-hides']==nil)
            assert(ns.db.choices.blacksmithing.imperial==nil)
            assert(ns.db.choices.blacksmithing.bronze==nil)
            assert(ns.db.choices.alchemy['finish']=='mana')
            assert(ns.db.targets.alchemy==300 and ns.db.exports.alchemy[3371]==42)
            assert(ns.db.sourceDate==ns.SourceDate and ns.status:find('Retired'))''')

    def test_november17_enchanting_wand_and_dust_routes(self):
        self.check('''skills={{skillID=333,name='Enchanting',rank=70,maxRank=150}}; ns.Refresh()
            ns.SetTarget(100); ns.Render()
            assert(ns.plan.steps[1].to==85 and ns.plan.steps[1].recipes[1].crafts==21)
            assert(ns.plan.steps[2].from==85 and ns.plan.steps[2].recipes[1].crafts==15)
            assert(ns.plan.materials[1].name=='Strange Dust' and ns.plan.materials[1].quantity==51)
            skills[1].rank=110; ns.Refresh(); ns.SetTarget(150); ns.Render()
            ns.SetChoice('enchanting','early-path','essence'); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Greater Magic Wand')
            assert(ns.plan.steps[1].to==125 and ns.plan.steps[1].recipes[1].crafts==23)
            assert(ns.plan.steps[2].recipes[1].crafts==37)
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Simple Wood']==23 and mats['Lesser Magic Essence']==194)
            ns.SetChoice('enchanting','early-path','essence-trainer'); ns.Render()
            assert(ns.plan.steps[2].recipes[1].name=='Enchant Boots - Minor Stamina')
            assert(ns.plan.steps[2].recipes[1].crafts==25)''')

    def test_linked_spurs_and_conflicting_alternates_are_exclusive(self):
        self.check('''skills={{skillID=164,name='Blacksmithing',rank=215,maxRank=300}}; level=60; ns.Refresh()
            ns.SetTarget(270); ns.Render(); assert(ns.SetChoice('blacksmithing','spurs','spurs')); ns.Render()
            assert(ns.plan.steps[3].from==235 and ns.plan.steps[3].to==245)
            assert(ns.plan.steps[3].recipes[1].crafts==28)
            assert(ns.GroupForStep('blacksmithing',ns.plan.steps[3]).id=='spurs')
            local before=ns.ActiveChoices('blacksmithing').spurs
            local group,option=ns.FindChoice('blacksmithing','imperial','rapier')
            assert(ns.CompareChoice('blacksmithing',group,option))
            assert(ns.ActiveChoices('blacksmithing').spurs==before)
            assert(ns.SetChoice('blacksmithing','imperial','rapier')); ns.Render()
            assert(ns.ActiveChoices('blacksmithing').spurs==nil)
            local expected=215
            for _,s in ipairs(ns.plan.steps) do assert(s.from==expected); expected=s.to end
            assert(expected==270)
            assert(ns.SetChoice('blacksmithing','spurs','spurs'))
            assert(ns.ActiveChoices('blacksmithing').imperial==nil)
            assert(not ns.SetChoice('blacksmithing','spurs-late','spurs'))
            local selected=ns.NormalizeChoices('blacksmithing',{spurs='spurs',imperial='rapier'})
            assert(selected.spurs=='spurs' and selected.imperial==nil)''')

    def test_lockpicking_refreshed_full_route_and_retired_alchemy_path(self):
        self.check('''skills={{skillID=633,name='Lockpicking',rank=270,maxRank=300}}; level=60; ns.Refresh()
            ns.SetTarget(300); ns.Render()
            assert(ns.Guides.lockpicking.cap==300 and #ns.plan.steps==1)
            assert(ns.plan.steps[1].action:find('Slag Pit'))
            assert(not ns.plan.steps[1].action:find('BRD'))
            assert(not ns.FindChoice('alchemy','oil-mana','mana'))
            ns.db.choices.alchemy={['oil-mana']='mana',finish='mana'}
            ns.db.sourceDate='2026-11-15'; ns.db=nil; ns.LoadSettings()
            assert(ns.db.choices.alchemy['oil-mana']==nil and ns.db.choices.alchemy.finish=='mana')
            assert(ns.status:find('Retired'))''')

    def test_november18_craft_count_corrections(self):
        self.check('''skills={{skillID=171,name='Alchemy',rank=65,maxRank=150}}; ns.Refresh()
            ns.SetTarget(90); ns.Render()
            assert(ns.plan.steps[1].recipes[1].crafts==28)
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats.Earthroot==56 and mats.Peacebloom==28)
            skills={{skillID=202,name='Engineering',rank=1,maxRank=150}}; ns.Refresh()
            ns.SetTarget(75); ns.Render()
            mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Rough Stone']==52 and mats['Copper Bar']==58 and mats['Linen Cloth']==26)
            assert(mats['Rough Blasting Powder']==nil and mats['Handful of Copper Bolts']==nil)
            skills[1].rank=250; ns.Refresh(); ns.SetTarget(260); ns.Render()
            assert(ns.plan.steps[1].recipes[1].crafts==44 and ns.plan.materials[1].quantity==88)''')

    def test_first_aid_poultice_path_and_updated_starter(self):
        self.check('''skills={{skillID=129,name='First Aid',rank=1,maxRank=150}}; ns.Refresh()
            ns.SetTarget(75); ns.SetChoice('first-aid','starter','potions'); ns.Render()
            assert(ns.plan.steps[1].recipes[1].crafts==86)
            skills[1].rank=90; ns.Refresh(); ns.SetTarget(150); ns.Render()
            assert(ns.SetChoice('first-aid','journeyman','potions')); ns.Render()
            assert(#ns.plan.steps==2 and ns.plan.steps[1].to==125)
            assert(ns.plan.steps[1].recipes[1].name=='Simple Poultice')
            assert(ns.plan.steps[2].recipes[1].name=='Healing Potion')
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Spider Ichor']==54 and mats['Bottle of Dalaran Noir']==54)
            assert(mats.Bruiseweed==31 and mats['Hot Spices']==31 and mats['Wool Cloth']==nil)
            ns.SetChoice('first-aid','journeyman','default'); ns.Render()
            assert(ns.plan.steps[1].recipes[1].crafts==40 and ns.plan.steps[2].recipes[1].crafts==51)''')

    def test_imperial_unlock_and_early_leather_alternate(self):
        self.check('''skills={{skillID=164,name='Blacksmithing',rank=240,maxRank=300}}; ns.Refresh()
            ns.SetTarget(245); ns.Render()
            assert(ns.warningText:GetText():find('A Blue Light Bargain'))
            assert(not ns.warningText:GetText():find('quest skill gates are unverified'))
            skills={{skillID=165,name='Leatherworking',rank=30,maxRank=150}}; ns.Refresh()
            ns.SetTarget(115); ns.SetChoice('leatherworking','light-hides','kits'); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Light Armor Kit')
            assert(ns.plan.steps[2].recipes[1].name=='Embossed Leather Gloves')
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats['Light Hide']==10 and mats.Salt>=10)
            assert(ns.warningText:GetText():find('still need 10'))''')

    def test_blacksmithing_finishing_routes_and_recipe_quest_cost(self):
        self.check('''skills={{skillID=164,name='Blacksmithing',rank=245,maxRank=300}}; level=60; ns.Refresh()
            local function finish(choice)
                local plan=ns.Plan('blacksmithing',ns.player,300,{finish=choice})
                for _,item in ipairs(plan.materials) do
                    if item.name=='Thorium Bar' then return plan.steps[2].recipes[1].name,item.quantity end
                end
            end
            local name,bars=finish('default'); assert(name=='Radiant Boots' and bars==1068)
            name,bars=finish('thorium'); assert(name=='Imperial Plate Bracers' and bars==1482)
            name,bars=finish('imperial'); assert(name=='Imperial Plate Boots' and bars==1780)''')

if __name__=='__main__': unittest.main(verbosity=2)
