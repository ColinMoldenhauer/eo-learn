"""
Module with tasks that integrate with GeoDB

To use tasks from this module you have to install dependencies defined in `requirements-geodb.txt`.

Copyright (c) 2017- Sinergise and contributors
For the full list of contributors, see the CREDITS file in the root directory of this source tree.

This source code is licensed under the MIT license, see the LICENSE file in the root directory of this source tree.
"""

from typing import Any, Optional

from sentinelhub import CRS, BBox

from eolearn.core.types import FeatureSpec

from ..geometry_io import _BaseVectorImportTask


class GeoDBVectorImportTask(_BaseVectorImportTask):
    """A task for importing vector data from `geoDB <https://eurodatacube.com/marketplace/services/edc_geodb>`__
    into EOPatch
    """

    def __init__(
        self,
        feature: FeatureSpec,
        geodb_client: Any,
        geodb_collection: str,
        geodb_db: str,
        reproject: bool = True,
        clip: bool = False,
        **kwargs: Any,
    ):
        """
        :param feature: A vector feature into which to import data
        :param geodb_client: an instance of GeoDBClient
        :param geodb_collection: The name of the collection to be queried
        :param geodb_db: The name of the database the collection resides in [current database]
        :param reproject: Should the geometries be transformed to coordinate reference system of the requested bbox?
        :param clip: Should the geometries be clipped to the requested bbox, or should be geometries kept as they are?
        :param kwargs: Additional args that will be passed to `geodb_client.get_collection_by_bbox` call
            (e.g. where="id>-1", operator="and")
        """
        self.geodb_client = geodb_client
        self.geodb_db = geodb_db
        self.geodb_collection = geodb_collection
        self.geodb_kwargs = kwargs
        self._dataset_crs: Optional[CRS] = None

        super().__init__(feature=feature, reproject=reproject, clip=clip)

    @property
    def dataset_crs(self) -> CRS:
        """Provides a "crs" of dataset, loads it lazily (i.e. the first time it is needed)

        :return: Dataset's CRS
        """
        if self._dataset_crs is None:
            srid = self.geodb_client.get_collection_srid(collection=self.geodb_collection, database=self.geodb_db)
            self._dataset_crs = CRS(f"epsg:{srid}")

        return self._dataset_crs

    def _load_vector_data(self, bbox: Optional[BBox]) -> Any:
        """Loads vector data from geoDB table"""
        prepared_bbox = bbox.transform_bounds(self.dataset_crs).geometry.bounds if bbox else None

        if "comparison_mode" not in self.geodb_kwargs:
            self.geodb_kwargs["comparison_mode"] = "intersects"

        return self.geodb_client.get_collection_by_bbox(
            collection=self.geodb_collection,
            database=self.geodb_db,
            bbox=prepared_bbox,
            bbox_crs=self.dataset_crs.epsg,
            **self.geodb_kwargs,
        )
