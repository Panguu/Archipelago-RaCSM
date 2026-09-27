import asyncio
import struct
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock

from .test_client_gameplay import GameMemory
from ..core.core import Core
from ..core.player_health_exp import PlayerHealthExpInventory, PLAYER_HEALTH_EXP, MAX_XP
from ..core.shrink_ray import ShrinkRaySkipInventory, SHRINK_RAY_GATE_ADDRESS
from ..core.scene_objects import discover
from ..core.ghost_ratchet import GhostRatchetInventory
from ..client.ghost_link import GhostLinkMixin
from ..core.address_maps import CURRENT_PLANET_ADDRESS
from ..core.structs.game import TransitionGateStruct
from ..constants.shrink_ray import SHRINK_RAY_PUZZLE_BITS, SHRINK_RAY_LOCATION_PLANETS
from ..core.giant_clank import STAGES


def scene(memory, base, signature, size):
    obj, matrix, definition, payload = base, base+0x100, base+0x1200, base+0x1300
    for address, value in ((obj+0x24,signature),(obj+12,matrix),(obj+16,definition),
        (matrix+0x40,obj),(matrix+0x58,payload),(definition+0x1c,size)):
        memory.write_int32(address,value)
    return SimpleNamespace(obj=obj,matrix=matrix,payload=payload,definition=definition)


class TestRemainingParity(unittest.TestCase):
    def setUp(self):
        self.memory=GameMemory()
        self.memory.get_game_id=lambda:'UCUS98633'

    def test_nanotech_boost_has_no_feedback_and_rebaselines_resets(self):
        state=PlayerHealthExpInventory(self.memory)
        state.multiplier=3
        self.memory.write_int32(PLAYER_HEALTH_EXP,100)
        state.apply_boost()
        self.memory.write_int32(PLAYER_HEALTH_EXP,110)
        state.apply_boost()
        self.assertEqual(self.memory.read_int32(PLAYER_HEALTH_EXP),130)
        state.apply_boost()
        self.assertEqual(self.memory.read_int32(PLAYER_HEALTH_EXP),130)
        self.memory.write_int32(PLAYER_HEALTH_EXP,5)
        state.apply_boost()
        self.assertEqual(self.memory.read_int32(PLAYER_HEALTH_EXP),5)
        state.abandon()
        self.memory.write_int32(PLAYER_HEALTH_EXP,1000)
        state.apply_boost()
        self.assertEqual(self.memory.read_int32(PLAYER_HEALTH_EXP),1000)

    def test_nanotech_overflow_and_adjacent_fields(self):
        state=PlayerHealthExpInventory(self.memory)
        state.multiplier=100
        self.memory.write_int32(PLAYER_HEALTH_EXP+4,2)
        self.memory.write_int32(PLAYER_HEALTH_EXP,MAX_XP-5)
        state.rebaseline()
        self.memory.write_int32(PLAYER_HEALTH_EXP,MAX_XP-1)
        state.apply_boost()
        self.assertEqual(self.memory.read_int32(PLAYER_HEALTH_EXP),MAX_XP)
        self.assertEqual(self.memory.read_int32(PLAYER_HEALTH_EXP+4),2)

    def test_all_puzzles_check_only_their_planet_and_replay_is_idempotent(self):
        state=ShrinkRaySkipInventory(self.memory)
        self.memory.write_int16(SHRINK_RAY_GATE_ADDRESS,0xffff)
        for planet in (3,7,8,9,10):
            expected={n for n,p in SHRINK_RAY_LOCATION_PLANETS.items() if p==planet}
            self.assertEqual(set(state.check(planet)),expected)
            self.assertEqual(state.check(planet),[])
        state.sync_from_ap(set(SHRINK_RAY_PUZZLE_BITS))
        self.assertEqual(state.check(3),[])

    def lock(self):
        lock=scene(self.memory,0x09000000,0x61b79aac,0x58)
        pv=0x09001800
        self.memory.write_int32(lock.matrix+0x54,pv)
        self.memory.write_int32(pv+12,0)
        self.memory.write_int32(lock.payload+4,lock.matrix)
        self.memory.write_int8(lock.payload+0x50,1)
        return lock

    def test_skip_changes_interlock_without_completing_puzzle_and_restores(self):
        lock=self.lock()
        state=ShrinkRaySkipInventory(self.memory)
        state.set_skip(1,True)
        self.assertEqual(self.memory.read_int8(lock.payload+0x50),0)
        self.assertEqual(self.memory.read_int16(SHRINK_RAY_GATE_ADDRESS),0)
        state.set_skip(1,False)
        self.assertEqual(self.memory.read_int8(lock.payload+0x50),1)
        state.set_skip(1,True)
        self.memory.write_int16(SHRINK_RAY_GATE_ADDRESS,1)
        state.restore()
        self.assertEqual(self.memory.read_int8(lock.payload+0x50),0)

    def test_skip_never_changes_active_puzzle_or_stale_object(self):
        lock=self.lock()
        state=ShrinkRaySkipInventory(self.memory)
        self.memory.write_int32(lock.payload+0x4c,1)
        state.set_skip(1,True)
        self.assertEqual(self.memory.read_int8(lock.payload+0x50),1)
        self.memory.write_int32(lock.payload+0x4c,0)
        self.memory.write_int32(lock.payload+4,0)
        state.set_skip(1,True)
        self.assertEqual(self.memory.read_int8(lock.payload+0x50),1)

    def test_ghost_requires_reciprocal_links_and_restores_display(self):
        player=scene(self.memory,0x09000000,0x36919224,4)
        ghost=scene(self.memory,0x09003000,0x0805c334,0x18c)
        self.memory.write_int32(ghost.matrix+0x64,0x8000)
        self.memory.write_bytes(player.matrix+0x30,struct.pack('<3f',1,2,3))
        state=GhostRatchetInventory(self.memory)
        self.assertEqual(state.read_own_position(1),(1,2,3))
        self.assertTrue(state.follow(1,4,5,6))
        self.assertEqual(self.memory.read_int32(ghost.payload),player.matrix)
        self.assertEqual(struct.unpack('<3f',self.memory.read_bytes(ghost.matrix+0x30,12)),(4,5,6))
        state.stop_following()
        self.assertEqual(self.memory.read_int32(ghost.matrix+0x64),0x8000)
        self.memory.write_int32(ghost.matrix+0x40,0)
        self.assertFalse(state.follow(1,4,5,6))

    def test_ghost_loading_and_nonfinite_positions_never_write(self):
        state=GhostRatchetInventory(self.memory)
        before=bytes(self.memory.data)
        self.assertFalse(state.follow(1,float('nan'),2,3))
        self.assertEqual(bytes(self.memory.data),before)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS,0)
        before=bytes(self.memory.data)
        self.assertFalse(state.follow(1,1,2,3))
        state.stop_following()
        self.assertEqual(bytes(self.memory.data),before)

    def test_giant_clank_stages_collect_once_and_keep_ratchet_unbound(self):
        core=Core(self.memory)
        core.clank_enabled=False
        core.planet.giant_clank_allowed=True
        core.planet.unlock_armour={'electroshock':1}
        for planet,(piece,locations) in STAGES.items():
            self.memory.write_int8(CURRENT_PLANET_ADDRESS,planet)
            core.send_location=Mock()
            core.tick()
            self.assertFalse(core.planet.is_ready)
            self.assertIsNone(core.planet.player.health_addr)
            core.armour.UnlockedArmour.electroshock=piece
            core.tick()
            core.tick()
            self.assertEqual([c.args[0] for c in core.send_location.call_args_list],list(locations))
        self.memory.write_int8(CURRENT_PLANET_ADDRESS,1)
        core.giant_clank.tick()
        self.assertEqual(int(core.armour.UnlockedArmour.electroshock),1)


class GhostHarness(GhostLinkMixin):
    def __init__(self):
        self._init_ghost_link()
        self.team=1
        self.slot=2
        self.game='PSP'
        self.tags=set()
        self.slot_info={2:SimpleNamespace(game='PSP'),3:SimpleNamespace(game='PSP'),4:SimpleNamespace(game='Other')}
        self.send_msgs=AsyncMock()
        self.set_notify=Mock()
        self._wiring=SimpleNamespace(planet=SimpleNamespace(is_ready=True,planet_id=1),ghost_ratchet=Mock())
        self._wiring.ghost_ratchet.read_own_position.return_value=(1.,2.,3.)


class TestGhostLinkProtocol(unittest.IsolatedAsyncioTestCase):
    async def test_opt_in_slot_filter_disable_and_broadcast(self):
        ctx=GhostHarness()
        ctx._poll_ghost_link()
        ctx.send_msgs.assert_not_called()
        await ctx._set_ghost_link_enabled(True)
        self.assertEqual(ctx._ghost_link_watched,{3})
        ctx._poll_ghost_link()
        await asyncio.sleep(0)
        value=ctx.send_msgs.call_args.args[0][0]['operations'][0]['value']
        self.assertEqual(value,{'planet_id':1,'x':1.,'y':2.,'z':3.})
        await ctx._set_ghost_link_enabled(False)
        self.assertEqual(ctx.send_msgs.call_args.args[0][0]['operations'][0]['value'],{})

    async def test_malformed_unrelated_and_stale_peers(self):
        ctx=GhostHarness()
        await ctx._set_ghost_link_enabled(True)
        key=ctx._ghost_link_key(3)
        good={'planet_id':1,'x':1,'y':2,'z':3}
        ctx._ghost_link_packet('SetReply',{'key':key,'value':good})
        ctx._poll_ghost_link()
        ctx._wiring.ghost_ratchet.follow.assert_called_once_with(1,1,2,3)
        ctx._ghost_link_packet('SetReply',{'key':'unrelated','value':good})
        ctx._ghost_link_peers[3]=(1,(1,2,3),0)
        ctx._poll_ghost_link()
        ctx._wiring.ghost_ratchet.stop_following.assert_called()
        for bad in ({},dict(good,x=float('inf')),dict(good,y=True),dict(good,planet_id=True)):
            ctx._ghost_link_packet('SetReply',{'key':key,'value':bad})
            self.assertNotIn(3,ctx._ghost_link_peers)


class TestGiantReturnPatch(unittest.TestCase):
    def setUp(self):
        from contextlib import nullcontext
        from ..core.patches.giant_clank import GiantClankReturn, PROFILE
        self.memory = GameMemory()
        self.memory.get_game_id = lambda: 'UCUS98633'
        self.memory.paused = nullcontext
        self.memory.invalidate_code = Mock()
        self.memory.write_int8(CURRENT_PLANET_ADDRESS, 15)
        self.state = GiantClankReturn(self.memory)
        self.address = 0x09000000 + PROFILE['offset']
        words = [0x0c000000 | (((0x09000000 + ((w & 0x3ffffff) << 2)) >> 2) & 0x3ffffff)
                 if w >> 26 == 3 else w for w in PROFILE['words']]
        self.original = struct.pack('<37I', *words)
        self.memory.write_bytes(self.address, self.original)

    def test_return_destination_and_disable_restore(self):
        self.state.tick(15, True)
        self.assertEqual(self.memory.read_int32(self.address + 20), 0x34100004)
        self.state.tick(15, True)
        self.state.tick(15, False)
        self.assertEqual(self.memory.read_bytes(self.address, 148), self.original)
        self.assertGreaterEqual(self.memory.invalidate_code.call_count, 2)

    def test_changed_call_and_duplicate_routine_refuse_all_writes(self):
        self.memory.write_int32(self.address + 15*4, 0)
        before = bytes(self.memory.data)
        with self.assertRaises(RuntimeError):
            self.state.tick(15, True)
        self.assertEqual(bytes(self.memory.data), before)
        self.state.restore()
        self.memory.write_bytes(self.address, self.original)
        self.memory.write_bytes(self.address + 0x1000, self.original)
        before = bytes(self.memory.data)
        with self.assertRaises(RuntimeError):
            self.state.tick(15, True)
        self.assertEqual(bytes(self.memory.data), before)

    def test_loading_drops_stale_plan_and_rebinds_reloaded_overlay(self):
        self.state.tick(15, True)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0)
        before = bytes(self.memory.data)
        self.state.tick(15, True)
        self.assertEqual(bytes(self.memory.data), before)
        self.assertIsNone(self.state.plan)
        self.memory.write_bytes(self.address, self.original)
        self.memory.write_int32(TransitionGateStruct.BASE_ADDRESS, 0xffffffff)
        self.state.tick(15, True)
        self.assertEqual(self.memory.read_int32(self.address + 20), 0x34100004)
