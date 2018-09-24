function createMap(dom_target) {
    var map = new ol.Map({
        target: dom_target,
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            })

        ],
        view: new ol.View({
          center: ol.proj.fromLonLat([37.41, 8.82]),
          zoom: 4
        })
    });
}
