import os
import string
import tempfile
from subprocess import call, Popen, PIPE

import numpy as np
from c_code import generate_c_code

_my_path = os.path.dirname(os.path.abspath(__file__))

def execute(stages, x):
    tmp_path = tempfile.mkdtemp(prefix='tmp_c_code', dir=_my_path)
    generate_main_c(tmp_path, stages, x)
    generate_workspace_h(tmp_path)
    generate_stage_h(tmp_path, stages)
    call('gcc --std=c99 -O3 main.c -o main'.split(), cwd=tmp_path)
    in_bytes = np.asarray(x, np.float32, 'C').tobytes()
    print(len(in_bytes))
    p = Popen('./main', cwd=tmp_path, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out_bytes, err = p.communicate(in_bytes)
    assert len(err) == 0
    y = np.frombuffer(out_bytes, np.float32)
    return y.reshape(x.shape[:3] + stages[-1].sink_values[0].shape)

def generate_main_c(path, stages, x):
    ni, nj, nk = x.shape[:3]
    max_vars = max([s.source_values[0].size for s in stages[1:]])
    assert np.prod(x.shape[3:]) == stages[0].source_values[0].size
    num_inputs = stages[0].source_values[0].size
    num_outputs = stages[-1].sink_values[0].size

    names = ['stage_{0}'.format(i) for i in range(len(stages))]
    include = '\n'.join(['#include "{0}.h"'.format(n) for n in names])
    stages = '\n'.join(['{0}(NI,NJ,NK,&buf);'.format(n) for n in names])

    template = open(os.path.join(_my_path, 'c_template', 'main.c')).read()
    template = string.Template(template)
    code = template.substitute(NI=ni, NJ=nj, NK=nk, MAX_VARS=max_vars,
                               NUM_INPUTS=num_inputs, NUM_OUTPUTS=num_outputs,
                               INCLUDE=include, STAGES=stages)
    with open(os.path.join(path, 'main.c'), 'wt') as f:
        f.write(code)

def generate_workspace_h(path):
    code = open(os.path.join(_my_path, 'c_template', 'workspace.h')).read()
    with open(os.path.join(path, 'workspace.h'), 'wt') as f:
        f.write(code)

def generate_stage_h(path, stages):
    for s in stages:
        assert len(s.source_values) == len(s.sink_values) == 1
    template = open(os.path.join(_my_path, 'c_template', 'stage.h')).read()
    template = string.Template(template)
    max_vars = max([s.source_values[0].size for s in stages[1:]])
    for i, s in enumerate(stages):
        stage_name = 'stage_{0}'.format(i)
        code = generate_c_code(s)
        num_inputs = s.source_values[0].size
        num_outputs = s.sink_values[0].size
        code = template.substitute(
                MAX_VARS=max_vars, STAGE_NAME=stage_name,
                NUM_INPUTS=num_inputs, NUM_OUTPUTS=num_outputs, CODE=code)
        with open(os.path.join(path, stage_name + '.h'), 'wt') as f:
            f.write(code)