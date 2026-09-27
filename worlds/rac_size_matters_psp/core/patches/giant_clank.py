"""Return Giant Clank Metalis to Metalis using its verified travel routine."""
import json
import struct
from importlib.resources import files
from .code import CodePlan
from .plan import Patch
from ..scene_objects import START, END, ready

PROFILE=json.loads(files(__package__.split('.core')[0]).joinpath('data','psp_giant_travel.json').read_text())


class GiantClankReturn:
    def __init__(self,memory):
        self.memory=memory
        self.plan=None
        self.attempted=False

    def tick(self,planet,enabled):
        if planet != 15:
            self.plan=None
            self.attempted=False
            return
        if not ready(self.memory,15):
            self.plan = None
            self.attempted = False
            return
        if not enabled:
            self.restore()
            return
        if self.attempted:
            return
        self.attempted=True
        with self.memory.paused():
            self.memory.invalidate_code()
            raw=self.memory.read_bytes(START,END-START)
            anchor=struct.pack('<6I',*PROFILE['words'][:6])
            hit=raw.find(anchor)
            if hit<0 or raw.find(anchor,hit+1)>=0:
                raise RuntimeError('Cannot identify Giant Clank travel routine')
            address=START+hit
            base=address-PROFILE['offset']
            actual=struct.unpack('<37I',raw[hit:hit+148])
            # Relocated JAL targets and LUI/load pairs vary with module base.
            for index,(word,retail) in enumerate(zip(actual,PROFILE['words'])):
                opcode=retail>>26
                if opcode==3:
                    expected=0x0c000000|(((base+((retail&0x3ffffff)<<2))>>2)&0x3ffffff)
                    if word!=expected:
                        raise RuntimeError('Giant Clank travel call changed')
                elif index in (6,7,8,9):
                    if word&0xffff0000!=retail&0xffff0000:
                        raise RuntimeError('Giant Clank travel globals changed')
                elif word!=retail:
                    raise RuntimeError('Giant Clank travel signature changed')
            self.plan=CodePlan(self.memory,[Patch(address+20,struct.pack('<I',0x00808025),
                struct.pack('<I',0x34100004))],name='Giant Clank return to Metalis',planet_id=15)
            self.plan.install()

    def restore(self):
        if self.plan and ready(self.memory,15):
            self.plan.restore()
        self.plan=None
        self.attempted=False
