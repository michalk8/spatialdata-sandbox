##
import os
from spatialdata_io import mcmicro
import shutil

##
f = 'data/exemplar-001'
assert os.path.isdir(f)
sdata = mcmicro(f)
print(sdata)
sdata.table.obs.index.name = 'index'

outfile = 'exemplar_001.zarr'
if os.path.exists(outfile):
    shutil.rmtree(outfile)
sdata.write(outfile)

from napari_spatialdata import Interactive
Interactive(sdata)