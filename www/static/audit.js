var map1, map2, marker1, marker2, smarker1, smarker2, feature, keys, lastView, defaultTitle, svButton;

if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position){
      position = position || 0;
      return this.substr(position, searchString.length) === searchString;
  };
}

$(function() {
  map1 = L.map('map1', {minZoom: AP.readonly ? 4 : 15, maxZoom: 19, zoomControl: false, attributionControl: false});
  L.control.permalinkAttribution().addTo(map1);
  map1.attributionControl.setPrefix('');
  map1.setView([20, 5], 7, {animate: false});

  var imageryLayers = {
    "OSM": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://openstreetmap.org">OpenStreetMap contributors</a>', maxZoom: 19
    }),
    'swisstopo SWISSIMAGE': L.tileLayer("https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swissimage/default/current/3857/{z}/{x}/{y}.jpeg", {
      attribution: '<a>Federal Office of Topography swisstopo</a>', maxZoom: 22
    }),
    'Esri': L.tileLayer('https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: '<a href="https://wiki.openstreetmap.org/wiki/Esri">Esri World Imagery</a>', maxZoom: 22
    }),
  };
  imageryLayers['OSM'].addTo(map1);

  var miniMap;
  if ($('#map2').length && $('#map2').is(':visible')) {
    map2 = L.map('map2', {minZoom: AP.readonly ? 4 : 15, maxZoom: 19, zoomControl: false});
    map2.attributionControl.setPrefix('');
    map2.setView([20, 5], 7, {animate: false});
    var miniLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://openstreetmap.org">© OpenStreetMap contributors</a>', maxZoom: 19
    });
    miniMap = new L.Control.MiniMap(miniLayer, {
      position: 'topright',
      height: 100,
      zoomLevelOffset: -6,
      minimized: true
    }).addTo(map2);

    delete imageryLayers['OSM'];
    imageryLayers['swisstopo SWISSIMAGE'].addTo(map2);

    var move = true;
    map1.on('move', function() {
      if (move) {
        move = false;
        map2.setView(map1.getCenter(), map1.getZoom(), { animate: false });
        move = true;
      }
    });
    map2.on('move', function() {
      if (move) {
        move = false;
        map1.setView(map2.getCenter(), map2.getZoom(), { animate: false });
        move = true;
      }
    });
  }

  L.control.zoom({position: map2 ? 'topright' : 'topleft'}).addTo(map1);
  L.control.layers(imageryLayers, {}, {collapsed: false, position: 'bottomright'}).addTo(map2 || map1);
  /*if (map2 && L.streetView) {
    svOptions = { position: 'bottomright' };
    if (!AP.proprietarySV)
      svOptions.google = false;
    if (AP.mapillaryId)
      svOptions.mapillaryId = AP.mapillaryId;
    svButton = L.streetView(svOptions).addTo(map2);
  }*/
  var popups = $('#popup').length > 0;

  if (AP.readonly && features) {
    var fl = L.markerClusterGroup({
          showCoverageOnHover: false,
          maxClusterRadius: function(zoom) { return zoom < 15 ? 40 : 10; }
        }),
        iconRed = new L.Icon({
          iconUrl: AP.imagesPath + '/marker-red.png',
          shadowUrl: AP.imagesPath + '/marker-shadow.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          shadowSize: [41, 41]
        }),
        iconGreen = new L.Icon({
          iconUrl: AP.imagesPath + '/marker-green.png',
          shadowUrl: AP.imagesPath + '/marker-shadow.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          shadowSize: [41, 41]
        });
    for (var i = 0; i < features.length; i++) {
      var action = features[i][2],
          icon = action == 'c' ? iconGreen : (action == 'd' ? iconRed : new L.Icon.Default()),
          m = L.marker(features[i][1], {icon: icon});
      m.ref = features[i][0];
      if (!popups) {
        m.on('click', function(e) {
          querySpecific(e.target.ref);
        });
      } else {
        m.bindPopup('... downloading ...');
        m.on('popupopen', function(e) {
          queryForPopup(e.target);
        });
        m.on('popupclose', hidePoint);
      }
      fl.addLayer(m);
    }
    map1.addLayer(fl);
    map1.fitBounds(fl.getBounds());
  }

  defaultTitle = $('#title').html();
  $('#hint').hide();
  $('#last_action').hide();
  $('#remarks_box').hide();
  map1.on('zoomend', function() {
    if (map1.getZoom() >= 10) {
      if (AP.readonly) {
        $('#zoom_out').show();
        $('#zoom_all').show();
      }
      if (miniMap)
        miniMap._setDisplay(false);
    } else {
      if (AP.readonly) {
        hidePoint();
        $('#zoom_out').hide();
        $('#zoom_all').hide();
      }
      if (miniMap)
        miniMap._setDisplay(true);
    }
  });
  if (AP.readonly) {
    if ($('#editthis').length)
      $('#editthis').hide();
    $('#zoom_out').click(function() {
      hidePoint();
      if (lastView) {
        map1.setView(lastView[0], lastView[1]);
        lastView = null;
      } else if (map1.getZoom() >= 10)
        map1.zoomOut(5);
    });
    $('#zoom_all').click(function() {
      hidePoint();
      map1.fitBounds(fl.getBounds());
    });
    $('#random').click(function() { queryNext(); });
    if (!popups) {
      window.addEventListener('popstate', function(e) {
        querySpecific(e.state);
      });
    }

    var hash = L.hash ? L.hash(map1) : null;
    if (AP.forceRef) {
      if (popups) {
        fl.eachLayer(function(layer) {
          if (layer.ref == AP.forceRef) {
            fl.zoomToShowLayer(layer, function() {
              layer.openPopup();
            })
          }
        });
      } else
        querySpecific(AP.forceRef);
    } else if (hash)
      hash.update();
  } else {
    var $rb = $('#reason_box');
    $rb.hide();
    $('#bad').click(function() {
      $rb.show();
      $('#bad').hide();
      $('#skip').hide();
      $('#reason').focus();
    });
    $('#reason').keypress(function(e) {
      if (e.which == 13) {
        $('#submit_reason').click();
        return false;
      }
    });
    $('#good').click({good: true}, submit);
    $('#submit_reason').click({good: false, msg: 'reason'}, submit);
    $('#create').click({good: false, create: true, msg: 'reason'}, submit);
    $('#bad_dup').click({good: false, msg: 'Duplicate'}, submit);
    $('#bad_nosuch').click({good: false, msg: 'Not there'}, submit);
    $('#skip').click({good: true, msg: 'skip'}, submit);

    if (AP.forceRef)
      querySpecific(AP.forceRef);
    else
      queryNext();
  }
});

function queryNext(audit) {
  $.ajax(AP.endpoint + '/feature/' + AP.projectId, {
    contentType: 'application/json',
    data: audit == null ? (AP.readonly ? {browse: 1} : null) : JSON.stringify(audit),
    method: audit ? 'POST' : 'GET',
    dataType: 'json',
    error: function(x,e,h) { window.alert('Ajax error. Please reload the page.\n'+e+'\n'+h); hidePoint(); },
    success: function(data) { data.feature.ref = data.ref; displayPoint(data.feature, data.audit || {}); }
  });
}

function querySpecific(ref) {
  $.ajax(AP.endpoint + '/feature/' + AP.projectId, {
    contentType: 'application/json',
    data: {ref: ref},
    method: 'GET',
    dataType: 'json',
    error: function(x,e,h) { window.alert('Ajax error. Please reload the page.\n'+e+'\n'+h); hidePoint(); },
    success: function(data) { data.feature.ref = data.ref; displayPoint(data.feature, data.audit || {}); }
  });
}

function queryForPopup(target) {
  if (!target.isPopupOpen())
    target.openPopup();

  $.ajax(AP.endpoint + '/feature/' + AP.projectId, {
    contentType: 'application/json',
    data: {ref: target.ref},
    method: 'GET',
    dataType: 'json',
    error: function(x,e,h) { window.alert('Ajax error. Please reload the page.\n'+e+'\n'+h); },
    success: function(data) {
      data.feature.ref = data.ref;
      displayPoint(data.feature, data.audit || {}, true);
      if (target.isPopupOpen()) {
        target.setPopupContent($('#popup').html().replace(/id="[^"]+"/g, ''));
      } else
        hidePoint();
    }
  });
}

function setChanged(fast) {
  var $good = $('#good');
  if (!fast)
    $good.text('Record changes');
  else
    $good.text($.isEmptyObject(prepareAudit()) ? 'Good' : 'Record changes');
}

function updateMarkers(data, audit, panMap) {
  var movePos = audit['move'], latlon, rlatlon, rIsOSM = false,
      coord = data['geometry']['coordinates'],
      props = data['properties'],
      canMove = !AP.readonly && (props['can_move'] || props['action'] == 'create'),
      refCoord = props['action'] == 'create' ? coord : props['ref_coords'],
      wereCoord = props['were_coords'];

  if (!movePos || !refCoord || movePos == 'osm') {
    if (movePos == 'osm' && wereCoord)
      latlon = L.latLng(wereCoord[1], wereCoord[0]);
    else
      latlon = L.latLng(coord[1], coord[0]);
    if (wereCoord && movePos != 'osm') {
      rlatlon = L.latLng(wereCoord[1], wereCoord[0]);
      rIsOSM = true;
    } else
      rlatlon = refCoord ? L.latLng(refCoord[1], refCoord[0]) : null;
  } else if (movePos == 'dataset' && refCoord) {
    latlon = L.latLng(refCoord[1], refCoord[0]);
    if (wereCoord)
      rlatlon = L.latLng(wereCoord[1], wereCoord[0]);
    else
      rlatlon = L.latLng(coord[1], coord[0]);
    rIsOSM = true;
  } else if (movePos.length == 2) {
    latlon = L.latLng(movePos[1], movePos[0]);
    rlatlon = L.latLng(coord[1], coord[0]);
    rIsOSM = !wereCoord && props['action'] != 'create';
  }

  if (marker1)
    map1.removeLayer(marker1);
  if (marker2)
    map2.removeLayer(marker2);
  if (smarker1)
    map1.removeLayer(smarker1);
  if (smarker2)
    map2.removeLayer(smarker2);

  $('#hint').show();
  if (rlatlon && (props['action'] != 'create' || movePos)) {
    var smTitle = rIsOSM ? 'OSM location' : 'External dataset location';
    smarker1 = L.marker(rlatlon, {opacity: 0.4, title: smTitle, zIndexOffset: -100}).addTo(map1);
    if (map2)
      smarker2 = L.marker(rlatlon, {opacity: 0.4, title: smTitle, zIndexOffset: -100}).addTo(map2);
    $('#tr_which').text(rIsOSM ? 'OpenStreetMap' : 'external dataset');
    $('#transparent').show();
    if (panMap)
      map1.fitBounds([latlon, rlatlon], {maxZoom: 18});
  } else {
    $('#transparent').hide();
    if (panMap)
      map1.setView(latlon, 18);
  }

  if (svButton)
    svButton.fixCoord(latlon);

  var mTitle = rIsOSM ? 'New location after moving' : 'OSM object location',
      iconGreen = new L.Icon({
        iconUrl: AP.imagesPath + '/marker-green.png',
        shadowUrl: AP.imagesPath + '/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        shadowSize: [41, 41]
      }),
      mIcon = canMove ? iconGreen : new L.Icon.Default();
  if (map2)
    marker2 = L.marker(latlon, {draggable: canMove, title: mTitle, icon: mIcon}).addTo(map2);
  if (!AP.readonly) {
    marker1 = L.marker(latlon, {draggable: canMove, title: mTitle, icon: mIcon}).addTo(map1);

    if (canMove) {
      $('#canmove').show();

      var guideLayer = L.layerGroup();
      L.marker(latlon).addTo(guideLayer);
      L.marker(rlatlon).addTo(guideLayer);
      if (movePos && movePos.length == 2)
        L.marker([refCoord[1], refCoord[0]]).addTo(guideLayer);

      marker1.snapediting = new L.Handler.MarkerSnap(map1, marker1, {snapDistance: 8});
      marker1.snapediting.addGuideLayer(guideLayer);
      marker1.snapediting.enable();

      marker1.on('dragend', function() {
        map1.panTo(marker1.getLatLng());
        setChanged();
      });

      if (marker2) {
        marker2.snapediting = new L.Handler.MarkerSnap(map2, marker2, {snapDistance: 8});
        marker2.snapediting.addGuideLayer(guideLayer);
        marker2.snapediting.enable();

        var move = true;
        marker1.on('move', function () {
          if (move) {
            move = false;
            marker2.setLatLng(marker1.getLatLng());
            move = true;
          }
        });
        marker2.on('move', function () {
          if (move) {
            move = false;
            marker1.setLatLng(marker2.getLatLng());
            move = true;
          }
        });
        marker2.on('dragend', function() {
          map1.panTo(marker2.getLatLng());
          setChanged();
        });
      }
    } else {
      $('#canmove').hide();
    }
  }
}

function saveHistoryState(ref) {
  if (AP.readonly) {
    if (history.state != ref) {
      history.pushState(ref, ref + ' — ' + document.title,
        AP.browseTemplateUrl.replace('tmpl', encodeURIComponent(ref)));
    }
  } else {
    history.replaceState(ref, ref + ' — ' + document.title,
      AP.featureTemplateUrl.replace('tmpl', encodeURIComponent(ref)));
  }
}

function prepareSidebar(data, audit) {
  var ref = data.ref, props = data['properties'],
      remarks = props['remarks'];

  coord = data['geometry']['coordinates'],

  console.log(props)

  $('#good').text('Good');

  if (AP.readonly) {
    var $editThis = $('#editthis');
    if (map1.getZoom() <= 15)
      lastView = [map1.getCenter(), map1.getZoom()];
    if ($editThis.length) {
      $('#editlink').attr('href', AP.featureTemplateUrl.replace('tmpl', encodeURIComponent(data.ref)));
      $editThis.show();
    }
  } else {
    $('#browselink').attr('href', AP.browseTemplateUrl.replace('tmpl', encodeURIComponent(data.ref)));
  }

  function formatObjectRef(props) {
    return (props['osm_type'] == 'node' ? 'point' : 'polygon')
  }

  var title;
  if (props['action'] == 'create')
    title = 'Create new node';
  else if (props['action'] == 'delete')
    title = 'Delete ' + formatObjectRef(props);
  else if (props['were_coords'])
    title = 'Modify and move ' + formatObjectRef(props);
  else if (props['ref_coords'])
    title = 'Update tags on ' + formatObjectRef(props);
  else
    title = 'Mark ' + formatObjectRef(props) + ' as obsolete';
  $('#title').html(title);

  // Add View on Buttons
 
  $('#toMaptillery').attr('href', (`https://www.mapillary.com/app/?lat=${coord[1]}&lng=${coord[0]}&z=18`))
  $('#toBing').attr('href', (`https://www.bing.com/maps?cp=${coord[1]}~${coord[0]}&lvl=19&style=x&v=2`))
  
  if (props['action'] == 'create')
  $('#toOSM').attr('href', (`https://www.openstreetmap.org/#map=19/${coord[1]}/${coord[0]}`))
  else
  $('#toOSM').attr('href', ('https://www.openstreetmap.org/' + props['osm_type'] + '/' + props['osm_id']))

  $('#buttons button').each(function() { $(this).prop('disabled', false); });
  if (AP.readonly) {
    // TODO: show or hide "zoom" buttons depending on selected feature
  } else if (props['action'] == 'create') {
    $('#bad').hide();
    $('#bad_dup').show();
    $('#bad_nosuch').show();
    $('#skip').show();
    $('#good').focus();
  } else {
    $('#bad').show();
    $('#bad_dup').hide();
    $('#bad_nosuch').hide();
    $('#skip').show();
    $('#good').focus();
  }

  if (!AP.readonly) {
    $('#fixme_box').show();
    $('#fixme').val(audit['fixme'] || '');
    $('#fixme').on('input', function() { setChanged(true); });
    $('#reason').val(audit['comment'] || '');
  }

  var verdict = audit['comment'] || '';
  if (audit['create'])
    verdict = 'create new point instead';
  if (audit['skip'] && !verdict)
    verdict = '<empty>';
  if (verdict) {
    $('#last_verdict').text(verdict);
    $('#last_action').show();
  } else {
    $('#last_action').hide();
  }

  // render remarks, if any.
  if (remarks) {
    $('#remarks_box').show();
    $('#remarks_content').text(remarks);
  } else {
    $('#remarks_box').hide();
  }
}

function renderTagTable(data, audit, editNewTags) {
  var props = data['properties'];

  // Table of tags. First record the original values for unused tags
  var original = {};
  for (var key in props)
    if (key.startsWith('tags.'))
      original[key.substr(key.indexOf('.')+1)] = props[key];

  // Now prepare a list of [key, osm_value, new_value, is_changed]
  keys = [];
  var skip = {};
  for (var key in props) {
    if (key.startsWith('tags') || key.startsWith('ref_unused_tags')) {
      k = key.substr(key.indexOf('.')+1);
      if (!AP.readonly && (k == 'source' || k.startsWith('ref') || k == 'fixme') && !key.startsWith('ref_unused')) {
        if (k == 'fixme')
          $('#fixme').val(props[key]);
        keys.push([k, props[key]]);
        skip[k] = true;
      }
      else if (key.startsWith('tags_new.'))
        keys.push([k, '', props[key], true]);
      else if (key.startsWith('tags_deleted.'))
        keys.push([k, props[key], '', true]);
      else if (key.startsWith('ref_unused')) {
        keys.push([k, original[k], props[key], false]);
        skip[k] = true;
      } else if (key.startsWith('tags_changed.')) {
        var i = props[key].indexOf(' -> ');
        keys.push([k, props[key].substr(0, i), props[key].substr(i+4), true]);
      } else if (key.startsWith('tags.')) {
        if (editNewTags && props['action'] == 'create')
          keys.push([k, '', props[key], true]);
        else if (!skip[k])
          keys.push([k, props[key]]);
      }
    }
  }

  // Apply audit data
  for (var i = 0; i < keys.length; i++) {
    if (keys[i].length == 4) {
      if (audit['keep'] && audit['keep'].indexOf(keys[i][0]) >= 0)
        keys[i].push(false);
      else if (audit['override'] && audit['override'].indexOf(keys[i][0]) >= 0)
        keys[i].push(true);
      else
        keys[i].push(keys[i][3]);
    }
  }


  // Render the table
  function esc(s) {
    s = s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    if (s.startsWith('http://') || s.startsWith('https://'))
      s = '<a href="'+s+'" target="_blank">'+s+'</a>';
    return s;
  }
  keys.sort(function(a, b) {
    return a.length == b.length ? ((a[0] > b[0]) - (b[0] - a[0])) : a.length - b.length;
  });


  function buildTable() {
    var rows = '<tr><th>Tag</th><th>New</th><th>Old</th></tr>', notset = '<span class="notset">not set</span>'
    for(var i = 0; i < keys.length; i++){
      key = keys[i];
      if (key.length == 2) {
        rows += '<tr class="notagedit"><th>' + esc(key[0]) + '</th><td>' + esc(key[1]) + '</td></tr>';
      } else {
        rows += '<tr class="tagedit"><th>' + esc(key[0]) + '</th>';
        rows += '<td>' + (!key[2] ? notset : esc(key[2])) + '&nbsp;<input type="radio" name="r'+i+'" value="2-'+i+'"></td>';
        rows += '<td>' + (!key[1] ? notset : esc(key[1])) + '&nbsp;<input type="radio" name="r'+i+'" value="1-'+i+'"></td></tr>';
      }
    }
    $('#tags').empty().append(rows);
  }

  buildTable()
  // Set state of each row
  function cellColor(row, which) {
    if (which == 1)
      return row[1] == '' ? 'red' : 'yellow';
    if (which == 2)
      return row[2] == '' ? 'yellow' : 'green';
    return 'green';
  }

  var rowidx_to_td = {};
  $('#tags td').each(function() {
    var $radio = $(this).children('input');
    if (!$radio.length)
      return;
    var idx = +$radio.val().substr(2),
        which = +$radio.val()[0],
        row = keys[idx],
        selected = (which == 1 && !row[4]) || (which == 2 && row[4]);
    if (!rowidx_to_td[idx])
      rowidx_to_td[idx] = [null, null];
    rowidx_to_td[idx][which] = $(this);
    if (selected) {
      $radio.prop('checked', true);
      $(this).addClass(cellColor(row, which));
    }
    if (AP.readonly)
      $radio.hide();
    else {
      $(this).click(function() {
        $radio.prop('checked', true);
        $(this).addClass(cellColor(row, which));
        rowidx_to_td[idx][3-which].children('input').prop('checked', false);
        rowidx_to_td[idx][3-which].removeClass(cellColor(row, 3-which));
        keys[idx][4] = which == 2;
        setChanged();
      });
    }
  });
}

function displayPoint(data, audit, forPopup) {
  if (!data.ref) {
    window.alert('Received an empty feature. You must have validated all of them.');
    hidePoint();
    return;
  }
  feature = data;
  if (!forPopup)
    saveHistoryState(data.ref);
  updateMarkers(data, audit, !forPopup);
  prepareSidebar(data, audit);
  renderTagTable(data, audit, !forPopup);
}

function hidePoint() {
  $('#tags').empty();
  $('#hint').hide();
  $('#last_action').hide();
  $('#fixme_box').hide();
  $('#remarks_box').hide();
  $('#title').html(defaultTitle);
  if (marker2)
    map2.removeLayer(marker2);
  if (smarker1)
    map1.removeLayer(smarker1);
  if (smarker2)
    map2.removeLayer(smarker2);
  if (svButton)
    svButton.releaseCoord();
}

function prepareAudit(data) {
  var fixme = $('#fixme').val(),
      audit = {},
      maxd = 3, // max distance to register change in meters
      coord = feature['geometry']['coordinates'],
      osmCoord = feature['properties']['were_coords'],
      dataCoord = feature['properties']['ref_coords'],
      newCoordTmp = marker1.getLatLng(),
      newCoord = [L.Util.formatNum(newCoordTmp.lng, 7), L.Util.formatNum(newCoordTmp.lat, 7)];

  // Record movement
  function distance(c1, c2) {
    if (!c2)
      return 1000000;
    var rad = Math.PI / 180,
	lat1 = c1[1] * rad,
	lat2 = c2[1] * rad,
	a = Math.sin(lat1) * Math.sin(lat2) +
	    Math.cos(lat1) * Math.cos(lat2) * Math.cos((c2[0] - c1[0]) * rad);

    return 6371000 * Math.acos(Math.min(a, 1));
  }
  if (distance(newCoord, coord) > maxd) {
    if (distance(newCoord, osmCoord) < maxd)
      audit['move'] = 'osm';
    else if (distance(newCoord, dataCoord) < maxd)
      audit['move'] = 'dataset';
    else
      audit['move'] = newCoord;
  }

  // Record tag changes
  for (var i = 0; i < keys.length; i++) {
    if (keys[i][3] != keys[i][4]) {
      if (keys[i][4]) {
        if (!audit['override'])
          audit['override'] = []
        audit['override'].push(keys[i][0]);
      } else {
        if (!audit['keep'])
          audit['keep'] = []
        audit['keep'].push(keys[i][0]);
      }
    }
  }

  // Record fixme
  if (fixme)
    audit['fixme'] = fixme;

  // Record good/bad and comment
  if (data && !data.good) {
    if (data.create)
      audit['create'] = true;
    else
      audit['skip'] = true;
    if (data.msg)
      audit['comment'] = data.msg == 'reason' ? ($('#reason').val() || '') : data.msg;
  }

  return audit;
}

function submit(e) {
  // Send audit result and query the next feature
  var audit = prepareAudit(e.data);
  var properties = feature['properties'];
  $('#reason_box').hide();
  $('#buttons button').each(function() { $(this).prop('disabled', true); });
  queryNext([feature.ref, e.data.msg == 'skip' ? null : audit, properties]);
}
