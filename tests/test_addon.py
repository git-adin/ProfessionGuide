"""Run the shipped Lua 5.1 files with a deterministic UI/inventory harness."""
from pathlib import Path
import sys, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'.tools'))
sys.path.insert(0,str(ROOT/'.tools'))
from lupa.lua51 import LuaRuntime

FILES=['Data.lua','Routes.lua','Character.lua','Planner.lua','Integration.lua','UI.lua','Core.lua']

class AddonTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'tests/wow_mock.lua').read_text())
        self.lua.execute('''
            function UnitLevel() return level or 20 end
            function UnitFactionGroup() return 'Alliance' end
            skills={{skillID=171,name='Alchemy',rank=1,maxRank=75}}
            C_SkillInfo={GetNumSkillLines=function() return #skills end,
                GetSkillLineInfo=function(i) return skills[i] end}
            GetItemCount=function(id) return owned and owned[id] or 0 end
            C_Item.GetItemCount=GetItemCount
            local mt=getmetatable(UIParent).__index
            function mt:GetStringHeight() return 1000 end
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

if __name__=='__main__': unittest.main(verbosity=2)
