"""Run the shipped Lua 5.1 files with a deterministic UI/inventory harness."""
from pathlib import Path
import sys, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'.tools'))
sys.path.insert(0,str(ROOT/'.tools'))
from lupa.lua51 import LuaRuntime

FILES=['Data.lua','Routes.lua','Character.lua','Icons.lua','Choices.lua','Planner.lua','Integration.lua','UI.lua','Minimap.lua','Core.lua']

class AddonTests(unittest.TestCase):
    def setUp(self):
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
        ns=self.lua.table(); self.lua.globals().ns=ns
        for name in FILES: self.lua.execute((ROOT/name).read_text(encoding='utf-8'),'ProfessionGuide',ns)
        self.check("Fire('ADDON_LOADED','ProfessionGuide'); Fire('PLAYER_LOGIN')")

    def check(self,code): self.lua.execute(code)

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
        self.check('''writes=0; ItemFarmingToolDB={items={}}
            SlashCmdList.ITEMFARMINGTOOL=function() writes=writes+1 end
            ns.SetTarget(55); ns.Render(); assert(writes==0)
            skills[1].rank=20; Fire('SKILL_LINES_CHANGED'); Tick()
            assert(ns.plan.rank==20 and writes==0)
            Fire('PLAYER_LEVEL_UP'); Tick(); assert(writes==0)''')

    def test_opt_in_export_preserves_and_is_repeatable(self):
        self.check('''ItemFarmingToolDB={items={{id=2447,goal=999},{id=123,goal=7}}}; calls={}
            SlashCmdList.ITEMFARMINGTOOL=function(text)
                calls[#calls+1]=text
                local id,q=text:match('add (%d+) (%d+)')
                if id then table.insert(ItemFarmingToolDB.items,{id=tonumber(id),goal=tonumber(q)}) end
            end
            ns.SetTarget(10); ns.Render(); assert(#calls==0)
            assert(ns.Export(ns.plan)); assert(#calls==2)
            assert(ItemFarmingToolDB.items[1].goal==999 and ItemFarmingToolDB.items[2].goal==7)
            assert(ns.Export(ns.plan)); assert(#calls==3) -- show only, no duplicate writes
        ''')

    def test_export_capacity_preflight(self):
        self.check('''ItemFarmingToolDB={items={}}; writes=0
            for i=1,100 do table.insert(ItemFarmingToolDB.items,{id=i,goal=1}) end
            SlashCmdList.ITEMFARMINGTOOL=function() writes=writes+1 end
            ns.SetTarget(10); ns.Render(); assert(not ns.Export(ns.plan)); assert(writes==0)''')

    def test_no_optional_addon(self):
        self.check("ns.SetTarget(75); ns.Render(); assert(ns.plan); assert(not ns.CanExport()); assert(not ns.Export(ns.plan))")

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

    def test_tailoring_bolts_and_source_limit(self):
        self.check('''skills={{skillID=197,name='Tailoring',rank=1,maxRank=75}}; ns.Refresh()
            local p=ns.Plan('tailoring',ns.player,55); local mats={}
            for _,m in ipairs(p.materials) do mats[m.name]=m.quantity end
            assert(mats['Linen Cloth']==60 and mats['Bolt of Linen Cloth']==nil)
            skills[1].rank=225; ns.Refresh(); p=ns.Plan('tailoring',ns.player,300)
            mats={}; for _,m in ipairs(p.materials) do mats[m.name]=m.quantity end
            assert(mats['Runecloth']==1220 and mats['Rugged Leather']==172)
            assert(p.warnings[1]:find('265') and p.steps[#p.steps].to==265)''')

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
        folder=ROOT.parent/'ItemFarmingTool/ItemFarmingTool'
        if not folder.exists(): self.skipTest('Optional sibling ItemFarmingTool source unavailable')
        ift=self.lua.table(); self.lua.globals().ift=ift
        for name in ['Core.lua','UI.lua']:
            self.lua.execute((folder/name).read_text(encoding='utf-8'),'ItemFarmingTool',ift)
        self.check('''Fire('ADDON_LOADED','ItemFarmingTool'); Fire('PLAYER_LOGIN')
            assert(ift.AddItem('2447',100)); assert(ift.AddItem('2589',7))
            ns.SetTarget(10); ns.Render(); assert(ns.Export(ns.plan))
            assert(ift.Find(2447).goal==100 and ift.Find(2589).goal==7)
            assert(ift.Find(3371).goal==9); local total=#ift.db.items
            assert(ns.Export(ns.plan)); assert(#ift.db.items==total)''')

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
            assert(ns.notesText:GetText():find('Ainethil'))
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
            skills={{skillID=186,name='Mining',rank=125,maxRank=150}}; ns.Refresh()
            ns.SetTarget(175); ns.Render()
            assert(ns.recipeText:GetText()=='Gathering route')
            assert(ns.detailText:GetText():find('Thousand Needles'))
            assert(#ns.plan.materials==0 and not ns.exportButton.enabled)''')

    def test_workshop_complete_and_source_end_states(self):
        self.check('''ns.Command('show'); ns.SetTarget(1); ns.Render()
            assert(ns.recipeText:GetText()=='Target reached' and #ns.route==0)
            skills={{skillID=197,name='Tailoring',rank=265,maxRank=300}}; ns.Refresh()
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
        self.check('''assert(ns.minimapButton:IsShown() and ns.db.hidden)
            ItemFarmingToolDB={items={}}; writes=0
            SlashCmdList.ITEMFARMINGTOOL=function() writes=writes+1 end
            ns.SetTarget(120)
            ns.minimapButton:GetScript('OnClick')(); assert(ns.frame:IsShown())
            ns.minimapButton:GetScript('OnClick')(); assert(not ns.frame:IsShown())
            local count=#frames; ns.InitMinimapButton(); assert(#frames==count)
            assert(writes==0 and ns.minimapButton:GetScript('OnUpdate')==nil)
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
        self.check('''skills[1].rank=130; ns.Refresh(); ns.SetTarget(165); ns.Render()
            assert(ns.SetChoice('alchemy','oil-mana','mana')); ns.Render()
            assert(#ns.plan.steps==2)
            for _,s in ipairs(ns.plan.steps) do assert(s.recipes[1].name=='Lesser Mana Potion') end
            local mats={}; for _,m in ipairs(ns.plan.materials) do mats[m.name]=m.quantity end
            assert(mats.Mageroyal==42 and mats.Stranglekelp==42 and mats['Empty Vial']==42)
            assert(mats['Firefin Snapper']==nil and mats.Kingsblood==nil)
            assert(ns.choiceDelta:find('Reduces 40 Firefin Snapper'))
            ns.db=nil; ns.LoadSettings(); assert(ns.ActiveChoices('alchemy')['oil-mana']=='mana')
            assert(ns.SetChoice('alchemy','oil-mana','default')); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Fire Oil')''')

    def test_alternate_dropdown_comparison_and_no_target(self):
        self.check('''ns.Command('show'); skills[1].rank=130; ns.Refresh()
            assert(ns.optionButton:IsShown() and ns.plan==nil)
            ns.optionButton:GetScript('OnClick')(); assert(ns.alternateMenu:IsShown())
            local alternate=ns.alternateMenu.buttons[2]
            alternate:GetScript('OnClick')(alternate)
            assert(not ns.alternateMenu:IsShown() and ns.plan==nil)
            assert(ns.recipeText:GetText()=='Lesser Mana Potion')
            assert(not ns.exportButton.enabled)
            ns.SetTarget(165); ns.Render(); ns.compareButton:GetScript('OnClick')()
            assert(ns.compareText:IsShown() and ns.compareText:GetText():find('Firefin Snapper'))
            assert(ns.ActiveChoices('alchemy')['oil-mana']=='mana')
            ns.compareButton:GetScript('OnClick')(); assert(not ns.compareText:IsShown())''')

    def test_enchanting_consistent_paths_and_minimum_estimate(self):
        self.check('''skills={{skillID=333,name='Enchanting',rank=20,maxRank=150}}; ns.Refresh()
            ns.SetTarget(150); ns.Render()
            local defaults=ns.GetGuideSteps('enchanting')
            assert(defaults[4].recipes[1].name=='Enchant Bracer - Minor Stamina')
            assert(ns.SetChoice('enchanting','early-path','essence')); ns.Render()
            assert(ns.plan.steps[1].recipes[1].name=='Enchant Bracer - Minor Deflect')
            assert(ns.plan.steps[#ns.plan.steps].recipes[1].name=='Enchant 2H Weapon - Lesser Intellect')
            ns.SetChoice('enchanting','early-path','essence-trainer'); ns.Render()
            assert(ns.plan.steps[#ns.plan.steps].recipes[1].name=='Enchant Boots - Minor Stamina')
            skills[1].rank=250; ns.Refresh(); ns.SetTarget(265)
            ns.SetChoice('enchanting','lotus','strength'); ns.Render()
            assert(ns.detailText:GetText():find('At least 15 crafts'))
            assert(ns.warningText:GetText():find('Minimum craft count'))''')

    def test_leatherworking_linked_choices_compose(self):
        self.check('''skills={{skillID=165,name='Leatherworking',rank=30,maxRank=150}}; ns.Refresh()
            ns.SetTarget(125); ns.SetChoice('leatherworking','light-hides','hides')
            ns.SetChoice('leatherworking','medium-hides','leather'); ns.Render()
            local names={}; for _,s in ipairs(ns.plan.steps) do names[s.from]=s.recipes[1].name end
            assert(names[30]=='Cured Light Hide' and names[45]==nil)
            assert(names[100]=='Light Leather Pants' and names[80]=='Fine Leather Belt')
            assert(names[115]=='Dark Leather Pants' and names[120]=="Hillman's Leather Gloves")
            assert(ns.warningText:GetText():find('Keep 24'))''')

    def test_choice_requirements_faction_and_corrupt_saves(self):
        self.check('''skills={{skillID=197,name='Tailoring',rank=215,maxRank=225}}; ns.Refresh()
            ns.SetTarget(225); assert(ns.SetChoice('tailoring','bags','belts')); ns.Render()
            assert(ns.warningText:GetText():find('level 35'))
            assert(not ns.SetChoice('alchemy','invalid','invalid'))
            local found=false
            for _,g in ipairs(ns.Alternates.cooking) do for _,o in ipairs(g.options) do
                if o.faction=='Horde' then assert(not ns.SetChoice('cooking',g.id,o.id)); found=true end
            end end
            assert(found)
            ns.db.choices.invalid={bad='bad'}; ns.db.choices.alchemy={['oil-mana']='mana',bad='bad'}
            ns.db.exports={alchemy={['bad']='bad',[2447]=-1,[3371]=42}}
            ns.db=nil; ns.LoadSettings()
            assert(ns.db.choices.invalid==nil and ns.db.choices.alchemy.bad==nil)
            assert(ns.db.choices.alchemy['oil-mana']=='mana' and ns.db.exports.alchemy[3371]==42)
            assert(ns.db.exports.alchemy[2447]==nil)''')

    def test_comparisons_and_choices_do_not_write_farming_goals(self):
        self.check('''skills[1].rank=130; ns.Refresh(); ns.SetTarget(165); ns.Render()
            ItemFarmingToolDB={items={}}; writes=0
            SlashCmdList.ITEMFARMINGTOOL=function() writes=writes+1 end
            local group=ns.GroupForStep('alchemy',ns.selectedStep)
            local comparison=ns.CompareChoice('alchemy',group,group.options[2])
            assert(comparison:find('Adds 42 Stranglekelp') and ns.ActiveChoices('alchemy')['oil-mana']==nil)
            ns.SetChoice('alchemy','oil-mana','mana'); ns.Render()
            Fire('BAG_UPDATE_DELAYED'); Fire('SKILL_LINES_CHANGED'); Tick()
            assert(writes==0 and next(ns.db.exports)==nil)''')

    def test_previous_export_review_survives_reexport(self):
        folder=ROOT.parent/'ItemFarmingTool/ItemFarmingTool'
        if not folder.exists(): self.skipTest('Optional sibling ItemFarmingTool source unavailable')
        ift=self.lua.table(); self.lua.globals().ift=ift
        for name in ['Core.lua','UI.lua']:
            self.lua.execute((folder/name).read_text(encoding='utf-8'),'ItemFarmingTool',ift)
        self.check('''Fire('ADDON_LOADED','ItemFarmingTool'); Fire('PLAYER_LOGIN')
            skills[1].rank=130; ns.Refresh(); ns.SetTarget(165); ns.Render()
            assert(ns.Export(ns.plan)); assert(ift.Find(6359).goal==40)
            ns.SetChoice('alchemy','oil-mana','mana'); ns.Render()
            local review=ns.ExportReview(ns.plan)
            assert(review:find('Firefin Snapper') and review:find('needs 0'))
            assert(ift.Find(6359).goal==40)
            assert(ns.Export(ns.plan)); assert(ns.ExportReview(ns.plan):find('Firefin Snapper'))
            ift.RemoveItem(6359); assert(not ns.ExportReview(ns.plan):find('Firefin Snapper'))
            assert(ift.Find(3820).goal==42)''')

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

if __name__=='__main__': unittest.main(verbosity=2)
