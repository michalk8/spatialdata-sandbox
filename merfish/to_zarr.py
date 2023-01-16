##
import pyarrow as pa
import os
os.environ['USE_PYGEOS'] = '0'
import json
import numpy as np
import scanpy as sc
import shutil
from pathlib import Path
import spatialdata as sd
import imageio.v3 as iio
import pandas as pd

##
path = Path().resolve()
# luca's workaround for pycharm
if not str(path).endswith("merfish"):
    path /= "merfish"
    assert path.exists()
##
path_read = path / "data" / "processed"
path_write = path / "data.zarr"

##
cells = sc.read_h5ad(path_read / "cells.h5ad")
adata = sc.read_h5ad(path_read / "single_molecule.h5ad")
##
j = json.load(open(path_read / "image_transform.json", "r"))
image_translation = np.array([0., j["translation_y"], j["translation_x"]])
image_scale_factors = np.array([1., j["scale_factor_y"], j["scale_factor_x"]])

translation = sd.NgffTranslation(translation=image_translation)
scale = sd.NgffScale(scale=image_scale_factors)
composed = sd.NgffSequence([scale, translation])

img = iio.imread(path_read / "image.png")
img = np.expand_dims(img, axis=0)
img = sd.Image2DModel.parse(img, dims=("c", "y", "x"), transform=composed)
##
annotations = pd.DataFrame({'cell_type': pd.Categorical(adata.obsm["cell_type"])})
single_molecule = sd.PointsModel.parse(coords=adata.X, annotations=pa.Table.from_pandas(annotations))

expression = cells.copy()
del expression.obsm["region_radius"]
del expression.obsm["spatial"]
expression = sd.TableModel.parse(
    adata=expression,
    region="/shapes/cells",
    instance_key="cell_id",
    instance_values=np.arange(len(cells)),
)
xy = cells.obsm["spatial"]
regions = sd.ShapesModel.parse(
    coords=xy,
    shape_type='Circle',
    shape_size=cells.obsm["region_radius"],
)

adata_polygons = sd.PolygonsModel.parse(path_read / "anatomical.geojson", instance_key="region_id")

##
sdata = sd.SpatialData(
    table=expression,
    shapes={"cells": regions},
    points={"single_molecule": single_molecule},
    images={"rasterized": img},
    polygons={"anatomical": adata_polygons},
)
print(sdata)
##
if path_write.exists():
    shutil.rmtree(path_write)
sdata.write(path_write)
print("done")
print(f'view with "python -m napari_spatialdata view data.zarr"')
##
sdata = sd.SpatialData.read(path_write)
print(sdata)

for el in sdata._gen_elements():
    t = sd.get_transform(el)
    print(t.to_affine().affine)
print("read")
