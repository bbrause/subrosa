/* 
SUB ROSA v0.1
2019
   
author:  Jan Luhmann
license: GNU General Public License v3.0
*/

var selected_film;      // currently selected film
var compare_left_film;  // film selected for left part of detail view
var compare_right_film; // film selected for right part of detail view

// arbitrary standard weights
var weights = {
  "tokens" : 50,
  "postags" : 35,
  "stopwords" : 35,
  "tempo" : 25,
  "sentiment" : 75,
  "stylometric" : 100
};

// EventListeners for weight sliders
var sliders = document.getElementsByClassName("slider");

for(var i=0; i<(sliders.length); i++) {
  sliders[i].addEventListener('input', function() {
    var slider_id = this.getAttribute('id');
    document.getElementById(slider_id+'_weight').innerText = this.value;
    weights[slider_id] = this.value;
  });
};

// EventListener for Sentiment detail view
for (let id_ of ["sentiment_scale", "sentiment_window"]) {
  selector = document.getElementById(id_);
  selector.addEventListener("change", create_sentiment_graph);
};

// EventListener for Speech Tempo detail view
for (let id_ of ["speechtempo_scale", "speechtempo_window"]) {
  selector = document.getElementById(id_);
  selector.addEventListener("change", create_speechtempo_graph);
};

// EventListener for color selector
color_selector = document.getElementById("colorselect");
color_selector.addEventListener("change", update_graph);

// Update distances by current weights and get graph data
function update_graph(){
  $.ajax({url: "update_weights/" + Object.values(weights).join("_"), 
          type: 'POST',
          success:
    function(result){
      var graph_data = result;
      drawgraph(graph_data);
    }});
};

// Get similar films of film with given ID and generate graph
function add_similar_films(film_id){
  var number = $('select[id=numberselect]').val();
  var app_url = "/add_similar_films/" + film_id + "/" + number + "/" + Object.values(weights).join("_");

  if (film_id === ''){
    $( "#dialog" ).text(
      "Please enter a valid IMDb ID!"
    );
  } else {
    $( "#dialog" ).text( ""
    );
  }

  $.ajax({url: app_url, 
          type: 'POST',
          beforeSend: function(){
            document.getElementById("add_similar_films").innerText = "loading...";
            document.getElementById("add_similar_films_shortcut").innerText = "loading...";
          },
          complete: function(){
            document.getElementById("add_similar_films").innerText = "Add Similar Films";
            document.getElementById("add_similar_films_shortcut").innerText = "Add Similar Films";
            document.getElementById('film_search').value = '';
          },
          success:
    function(result){
      var graph_data = result;
      drawgraph(graph_data);
      for (f in graph_data.nodes){
        f = graph_data.nodes[f];
        if (f.id === parseInt(film_id)){
          display_film_infobox(f);
        }
      }
    }});
}

$(document).ready(function(){

  // get search data for Autocomplete search box
  $.ajax({url: "get_search_data",
          type: 'POST',
          success: function(result){
            $('#film_search').autocomplete({
              appendTo: "#autocomplete",
              source: function(request, response) {
                var options = {
                  shouldSort: true,
                  threshold: 0.3,
                  location: 0,
                  distance: 100,
                  maxPatternLength: 32,
                  minMatchCharLength: 1,
                  keys: [
                    "label"
                  ]
                };

                var f = new Fuse(result["results"], options);
                var search_result = f.search(request.term);

                response(search_result);
              },
              minLength: 1,
              delay: 600,
              select: function(event, ui) {
                var value = ui.item.value;
                var label = ui.item.label;
                this.value = label;
                $('#film_search_id').val(value);
                return false;
              }

            });
            }
          });

  // Update weights slider values
  for(var i=0; i<(sliders.length); i++) {
    var slider = sliders[i];
    var slider_id = slider.getAttribute('id');
    document.getElementById(slider_id+'_weight').innerText = slider.value;
    weights[slider_id] = slider.value;
  };

  // Various button requests
  $("#shutdown").click(function() {
    $.ajax({url: "/shutdown", 
              type: 'POST',
              success:
              window.close()
            });
  });

  $("button#compare_left").click(function() {
    display_compare("left", selected_film);
  });

  $("button#compare_right").click(function() {
    display_compare("right", selected_film);
  });

  $("button#clear").click(function() {
    $.ajax({url: "/clear"});
    clear();
  });

  $("button#add_film").click(function(){
    var film_id = $('input[id=film_search_id]').val();

    if (film_id === ''){
      $( "#dialog" ).dialog();
    }

    $.ajax({url: "/add_film/" + film_id, 
            type: 'POST',
            success:
      function(result){
        if (result === 'None' || result === 'Exists'){
          console.log("None");
        } else {
          var graph_data = result;
          drawgraph(graph_data);
          for (f in graph_data.nodes){
            f = graph_data.nodes[f];
            if (f.id === parseInt(film_id)){
              display_film_infobox(f);
            }
          }
        }
      }});
      document.getElementById('film_search').value = '';
      document.getElementById('film_search_id').value = '';
  });

  $("button#add_similar_films").click(function(){
    var film_id = $('input[id=film_search_id]').val();
    add_similar_films(film_id);
  });

  $("button#add_similar_films_shortcut").click(function(){
    add_similar_films(selected_film.id);
  });


  $("button#update").click(function(){
    update_graph();
  });

});


// Initialize graph
var svg = d3.select(".graph").append("svg");

resize();
d3.select(window).on('resize', resize); 

width = +svg.attr("width"),
height = +svg.attr("height");

var color_genre = d3.scaleOrdinal()
            .domain(["Sci-Fi", "Comedy", "Crime", "Horror", "Fantasy", "Western", "Action", "Drama", "Adventure", "Thriller"])
            .range(["#006ddb", "#ffff6d", "#b6dbff", "#001111", "#b66dff", "#924900", "#db6d00", "#920000", "#24ff24", "#004949"]);

var current_year = new Date().getFullYear();
var expScale = d3.scalePow()
    .exponent(2)
    .domain([1920, current_year + 2]);
var color_year = d3.scaleSequential(d3.interpolateMagma);

function color(d) {
  var mode = $('select[id=colorselect]').val();

  if (mode === "none") {
    return "#222";
  } else if (mode === "genre") {
    return color_genre(d.genre);
  } else if (mode === "year") {
    return color_year(expScale(d.year));
  }
};

function clear() {
  d3.selectAll(".graph > svg > *").remove();
  document.getElementsByClassName("infobox")[0].style.display = 'none';
  document.getElementsByClassName("comparebox")[0].style.display = 'none';
}

// Draw new graph
function drawgraph(data) {
  var t = d3.transition()
          .duration(750);

  d3.selectAll(".graph > svg > *").remove();

  data.links = data["links"];
  data.nodes = data["nodes"];

  resize();

  function linkDistance(d) {
    return 0.5 * Math.pow(d.distance, 2) * Math.sqrt((width*width) + (height*height));
  }
        
  var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) { return d.id; }).distance(linkDistance).strength(0.3))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2))
    .on("tick", ticked);

  var root = svg.append("g")
    .attr("class", "root")

  var link = root.append("g")
    .attr("class", "links")
    .selectAll("line")
    .data(data.links)
    .enter().append("line")
    .attr("stroke-width", 2); 
  
  var node = root.append("g")
      .attr("class", "nodes")
    .selectAll("g")
    .data(data.nodes)
    .enter().append("g")
    .call(d3.drag()
          .on("start", drag_start)
          .on("drag", drag_drag)
          .on("end", drag_end))
    .on("click", function(d){
            display_film_infobox(d);
          });
  
  var circles = node.append("circle")
      .attr("r", 5)
      .attr("fill", function(d) { return color(d); })
      

  var labels = node.append("text")
      .text(function(d) {
        return d.title + " (" + d.year + ")";
      })
      .attr('x', 6)
      .attr('y', 3);

  //Drag functions 
  //d is the node 
  function drag_start(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
  }
 
 //make sure you can't drag the circle outside the box
 function drag_drag(d) {
   d.fx = d3.event.x;
   d.fy = d3.event.y;
 }
 
 function drag_end(d) {
   if (!d3.event.active) simulation.alphaTarget(0);
   d.fx = null;
   d.fy = null;
 }
 
  var drag_handler = d3.drag()
    .on("start", drag_start)
    .on("drag", drag_drag)
    .on("end", drag_end);	
    
  drag_handler(node);

  var zoom_handler = d3.zoom()
    .on("zoom", zoom_actions)

  zoom_handler(svg);   

  //Zoom functions 
  function zoom_actions(){
      transform = d3.event.transform;
      root.attr("transform", transform);
      labels.style("font-size", 80 / transform.k + "%")
            .attr("x", 6 / transform.k)
            .attr("y", 3 / transform.k);
      circles.attr("r", 5 / transform.k);
      link.attr("stroke-width", 2 / transform.k);
  }
  
  function ticked() {
      var alpha = this.alpha();
      var chargeStrength;
    
        if ( alpha > 0.2 ) {
        chargeStrength = (alpha - 0.2 / 0.8);
      }
      else {
        chargeStrength = 0;
      }
    
      this.force("charge", d3.forceManyBody().strength( -30 * chargeStrength ))
      
      
        link
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        node
            .attr("transform", function(d) {
              return "translate(" + d.x + "," + d.y + ")";
            })
        
      // Validate given distance with realized distance
      if (alpha < 0.001) {
        link.each(function(d,i) {
        
          var a = d.source.x - d.target.x;
          var b = d.source.y - d.target.y;
            var c = Math.pow(a*a + b*b, 0.5);
          
          console.log("specified length: " + data.links[i].distance + ", realized distance: " + c );
        })
      }
      }
  
  simulation
      .nodes(data.nodes)
      .on("tick", ticked);

  simulation.force("link")
      .links(data.links);             
}

// Resize graphbox by size of window
function resize() {
  var graphbox = d3.select('.graphbox').node();
  width = graphbox.getBoundingClientRect().width - 20;
  height = graphbox.getBoundingClientRect().height - 20;
  svg.attr("width", width).attr("height", height);
}

// Infobox for a selected film
function display_film_infobox(film) {
  selected_film = film;
  document.getElementsByClassName("infobox")[0].style.display = 'inline';
  document.getElementById("film_title").innerText = film.title;
  document.getElementById("film_year").innerText = "(" + film.year + ")";
  document.getElementById("film_genres").innerText = "Genre: " + film.genres.join(", ");
  var zerofilled_id = ('000000'+film.id).slice(-7);
  var url = "https://www.imdb.com/title/tt" + zerofilled_id;
  document.getElementById("imdb_link").setAttribute('href', url);
  document.getElementById("imdb_link").innerText = 'on IMDb';
}

// Generate a term cloud of Bag-of-Words model detail view
function generate_token_cloud(cloud, tokens){
  while (cloud.lastChild) {
    cloud.removeChild(cloud.lastChild);
  } 
  for(let token of tokens) {
    if (token[0].length > 1){
      let span = document.createElement('span');
      span.innerText = token[0] + " ";
      span.style.fontSize = (100 + (token[1] * 20)) + "%";
      cloud.appendChild(span);
    }
  }
}

// Generate a detail view table
function generate_table(table_div, data){
  while (table_div.lastChild) {
    table_div.removeChild(table_div.lastChild);
  } 
  table = document.createElement('div');
  table.style.width = '100%';
  tbody = document.createElement('div');
  tbody.style.display = 'table-row-group';
  tbody.style.textAlign = 'center';
  table.appendChild(tbody);
  for (let row of data) {
    trow = document.createElement('div');
    trow.style.display = 'table-row';
    
    tcell = document.createElement('div');
    tcell.style.display = 'table-cell';
    tcell.style.padding = '0.33em';
    tcell.style.width = '10em';
    tcell.innerText = row[0];
    trow.appendChild(tcell);

    tcell = document.createElement('div');
    tcell.style.display = 'table-cell';
    tcell.style.padding = '0.33em';
    tcell.innerText = row[1].toFixed(2);
    trow.appendChild(tcell);
     
    tbody.appendChild(trow);
  }
  table_div.appendChild(table);
}

// Generate table for Stylometric model
function generate_stylometric_table(){
  var table_div = document.getElementById("stylometric_table");
  
  while (table_div.lastChild) {
      table_div.removeChild(table_div.lastChild);
  }

  var left = false;
  var right = false;

  if (typeof compare_left_film !== "undefined") {
    left = true;
  }
  if (typeof compare_right_film !== "undefined") {
    right = true;
  }
  
  feature_list = [
    ["entropy", "sttr", "mean_sentiment"],
    ["mean_sentence_length", "short_sentence_ratio", "mid_sentence_ratio", "long_sentence_ratio"],
    ["mean_word_length", "short_word_ratio", "mid_word_ratio", "long_word_ratio"],
    ["mean_words_per_second", "mean_silence_duration", "silence_ratio"],
  ]

  var first_row = [true, true];

  table = document.createElement('div');
  table.style.width = '100%';

  table_div.appendChild(table);

  for (let new_table_list of feature_list) {
    thead = document.createElement('div');
    thead.style.display = 'table-header-group';
    thead.style.textAlign = 'center';
    table.appendChild(thead);

    theaderrow = document.createElement('div');
    theaderrow.style.display = 'table-row';

    tcell = document.createElement('div');
    tcell.style.display = 'table-cell';
    tcell.style.padding = '0.33em';
    tcell.style.width = '10em';
    tcell.style.fontSize = "100%";
    tcell.innerText = "";
    theaderrow.appendChild(tcell);

    for (let key of new_table_list) {
        tcell = document.createElement('div');
        tcell.style.display = 'table-cell';
        tcell.style.padding = '0.33em';
        tcell.style.width = '10em';
        tcell.style.fontSize = "100%";
        tcell.style.fontWeight = 'bold';
        tcell.innerText = key;
        theaderrow.appendChild(tcell);
    }

    thead.appendChild(theaderrow);

    tbody = document.createElement('div');
    tbody.style.display = 'table-row-group';
    tbody.style.textAlign = 'center';
    table.appendChild(tbody);

    if (left) {
      trow = document.createElement('div');
      trow.style.display = 'table-row';

      tcell = document.createElement('div');
      tcell.style.display = 'table-cell';
      tcell.style.padding = '0.33em';
      tcell.style.width = '10em';
      tcell.style.fontSize = "100%";
      tcell.style.fontWeight = "bold";
      tcell.style.color = "darkred";
      if (first_row[0]) {
        tcell.innerText = compare_left_film.title;
        first_row[0] = false;
      } else {
        tcell.innerText = "";
      }
      trow.appendChild(tcell);

      for (let key of new_table_list) {
        tcell = document.createElement('div');
        tcell.style.display = 'table-cell';
        tcell.style.padding = '0.33em';
        tcell.style.width = '10em';
        tcell.style.fontSize = "100%";
        tcell.style.color = "darkred";
        tcell.innerText = compare_left_film.stylometric_features[key].toFixed(3);
        trow.appendChild(tcell);
      }
      tbody.appendChild(trow);
    }

    if (right) {
      trow = document.createElement('div');
      trow.style.display = 'table-row';

      tcell = document.createElement('div');
      tcell.style.display = 'table-cell';
      tcell.style.padding = '0.33em';
      tcell.style.width = '10em';
      tcell.style.fontSize = "100%";
      tcell.style.color = "blue";
      tcell.style.fontWeight = 'bold';
      if (first_row[1]) {
        tcell.innerText = compare_right_film.title;
        first_row[1] = false;
      } else {
        tcell.innerText = "";
      }
      trow.appendChild(tcell);

      for (let key of new_table_list) {
        tcell = document.createElement('div');
        tcell.style.display = 'table-cell';
        tcell.style.padding = '0.33em';
        tcell.style.width = '10em';
        tcell.style.fontSize = "100%";
        tcell.style.color = "blue";
        tcell.innerText = compare_right_film.stylometric_features[key].toFixed(3);
        trow.appendChild(tcell);
      }
      tbody.appendChild(trow);
    }
  }
}

// Create graph for Speech Tempo detail view
function create_speechtempo_graph() {
  var graph = document.getElementsByClassName("graph_speechtempo")[0];
    while (graph.lastChild) {
      graph.removeChild(graph.lastChild);
  }

  var cent_min = $('select[id=speechtempo_scale]').val();
  var window_size = $('select[id=speechtempo_window]').val();

  var svg_line = d3.select(".graph_speechtempo").append("svg")
      .attr('width', '100%')
      .attr('height', '250px')
      .attr('display', 'inline-block');

  var margin = {top: 10, right: 10, bottom: 40, left: 40},
    width = 450 - margin.left - margin.right,
    height = 250 - margin.top - margin.bottom;

  var y_data_left = [];
  var y_data_right = [];
  var extent_max = [4];

  if (typeof compare_left_film !== "undefined") {
    y_data_left = compare_left_film.speechtempo[cent_min][window_size];
    extent_max.push(d3.max(y_data_left));
  }
  if (typeof compare_right_film !== "undefined") {
    y_data_right = compare_right_film.speechtempo[cent_min][window_size];
    extent_max.push(d3.max(y_data_right));
  }
  
  var x_data = d3.range(0, window_size * Math.max(y_data_left.length, y_data_right.length), window_size);

  var xscl = d3.scaleLinear()
    .domain(d3.extent(x_data)) //use just the x part
    .range([margin.left, width + margin.left]);

  var yscl = d3.scaleLinear()
    .domain([0, d3.max(extent_max)])
    .range([height + margin.top, margin.top]);

  var myline = d3.line()
    .x(function(d) { return xscl(d.x);}) // apply the x scale to the x data
    .y(function(d) { return yscl(d.y);})
    .curve(d3.curveMonotoneX);

  svg_line.append('rect') // outline for reference
    .attr("x", margin.left)
    .attr("y", margin.top)
    .attr("width", width)
    .attr("height", height)
    .attr("stroke", 'black')
    .attr('stroke-width', 0.5)
    .attr("fill",'white'); 

  if (y_data_left.length > 0){
    var xy_data_left = [];
    for(var i = 0; i < y_data_left.length; i++) {
      xy_data_left.push({x: x_data[i], y: y_data_left[i]});
    }

    svg_line.append("path")
      .attr("class", "line") // attributes given one at a time
      .attr("d", myline(xy_data_left)) // use the value of myline(xy) as the data, 'd'
      .style("fill", "none")
      .style("stroke", "darkred")
      .style("stroke-width", 1);

    svg_line.append("circle").attr("cx",width + margin.right + margin.left + 20).attr("cy",height / 2).attr("r", 5).style("fill", "darkred");
    svg_line.append("text").attr("x", width + margin.right + margin.left + 30).attr("y", height / 2).text(compare_left_film.title).style("font-size", "90%").attr("alignment-baseline","middle");
  }

  if (y_data_right.length > 0){
    var xy_data_right = [];
    for(var i = 0; i < y_data_right.length; i++) {
      xy_data_right.push({x: x_data[i], y: y_data_right[i]});
    }
    
    svg_line.append("path")
      .attr("class", "line") // attributes given one at a time
      .attr("d", myline(xy_data_right)) // use the value of myline(xy) as the data, 'd'
      .style("fill", "none")
      .style("stroke", "blue")
      .style("stroke-width", 1);

    svg_line.append("circle").attr("cx",width + margin.right + margin.left + 20).attr("cy",(height / 2) + 30).attr("r", 5).style("fill", "blue");
    svg_line.append("text").attr("x", width + margin.right + margin.left + 30).attr("y", (height / 2) + 30).text(compare_right_film.title).style("font-size", "90%").attr("alignment-baseline","middle");
  }

  var yAxis = d3.axisLeft()
      .scale(yscl);

  var xAxis = d3.axisBottom()
      .scale(xscl);

  svg_line.append("g")
      .attr("transform", "translate(0," + (height + margin.top)  + ")")
      .call(xAxis);

  svg_line.append("g")
      .attr("transform", "translate(" + margin.left + ",0)")
      .call(yAxis);

  svg_line.append("text")             
      .attr("transform", "rotate(-90)")
      .attr("y", 0)
      .attr("x",0 - (height / 2) - margin.top)
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("words per second");

  if (cent_min === "percent") {
    svg_line.append("text")             
      .attr("transform",
            "translate(" + (width/2 + margin.left) + " ," + 
                           (height + margin.top + 30) + ")")
      .style("text-anchor", "middle")
      .text("% of runtime");
  } else {
    svg_line.append("text")             
      .attr("transform",
            "translate(" + (width/2 + margin.left) + " ," + 
                           (height + margin.top + 30) + ")")
      .style("text-anchor", "middle")
      .text("minutes of runtime");
  }
};

// Create graph for Sentiment detail view
function create_sentiment_graph(cent_min, window_size) {
  var graph = document.getElementsByClassName("graph_sentiment")[0];
    while (graph.lastChild) {
      graph.removeChild(graph.lastChild);
  }

  var cent_min = $('select[id=sentiment_scale]').val();
  var window_size = $('select[id=sentiment_window]').val();

  var svg_line = d3.select(".graph_sentiment").append("svg")
      .attr('width', '100%')
      .attr('height', '250px')
      .attr('display', 'inline-block');

  var margin = {top: 10, right: 10, bottom: 40, left: 40},
    width = 450 - margin.left - margin.right,
    height = 250 - margin.top - margin.bottom;

  var y_data_left = [];
  var y_data_right = [];
  var extent_min = [-0.5];
  var extent_max = [0.5];

  if (typeof compare_left_film !== "undefined") {
    y_data_left = compare_left_film.sentiment[cent_min][window_size];
    extent_min.push(d3.min(y_data_left));
    extent_max.push(d3.max(y_data_left));
  }
  if (typeof compare_right_film !== "undefined") {
    y_data_right = compare_right_film.sentiment[cent_min][window_size];
    extent_min.push(d3.min(y_data_right));
    extent_max.push(d3.max(y_data_right));
  }

  var x_data = d3.range(0, window_size * Math.max(y_data_left.length, y_data_right.length), window_size);

  var xscl = d3.scaleLinear()
    .domain(d3.extent(x_data)) //use just the x part
    .range([margin.left, width + margin.left]);

  var yscl = d3.scaleLinear()
    .domain([d3.min(extent_min), d3.max(extent_max)])
    .range([height + margin.top, margin.top]);

  var myline = d3.line()
    .x(function(d) { return xscl(d.x);}) // apply the x scale to the x data
    .y(function(d) { return yscl(d.y);})
    .curve(d3.curveMonotoneX);

  svg_line.append('rect') // outline for reference
    .attr("x", margin.left)
    .attr("y", margin.top)
    .attr("width", width)
    .attr("height", height)
    .attr("stroke", 'black')
    .attr('stroke-width', 0.5)
    .attr("fill",'white'); 

  if (y_data_left.length > 0){
    var xy_data_left = [];
    for(var i = 0; i < y_data_left.length; i++) {
      xy_data_left.push({x: x_data[i], y: y_data_left[i]});
    }

    svg_line.append("path")
      .attr("class", "line") // attributes given one at a time
      .attr("d", myline(xy_data_left)) // use the value of myline(xy) as the data, 'd'
      .style("fill", "none")
      .style("stroke", "darkred")
      .style("stroke-width", 1);

    svg_line.append("circle").attr("cx",width + margin.right + margin.left + 20).attr("cy",height / 2).attr("r", 5).style("fill", "darkred");
    svg_line.append("text").attr("x", width + margin.right + margin.left + 30).attr("y", height / 2).text(compare_left_film.title).style("font-size", "90%").attr("alignment-baseline","middle");
  }

  if (y_data_right.length > 0){
    var xy_data_right = [];
    for(var i = 0; i < y_data_right.length; i++) {
      xy_data_right.push({x: x_data[i], y: y_data_right[i]});
    }
    
    svg_line.append("path")
      .attr("class", "line") // attributes given one at a time
      .attr("d", myline(xy_data_right)) // use the value of myline(xy) as the data, 'd'
      .style("fill", "none")
      .style("stroke", "blue")
      .style("stroke-width", 1);

    svg_line.append("circle").attr("cx",width + margin.right + margin.left + 20).attr("cy",(height / 2) + 30).attr("r", 5).style("fill", "blue");
    svg_line.append("text").attr("x", width + margin.right + margin.left + 30).attr("y", (height / 2) + 30).text(compare_right_film.title).style("font-size", "90%").attr("alignment-baseline","middle");
  }

  var yAxis = d3.axisLeft()
      .scale(yscl);

  var xAxis = d3.axisBottom()
      .scale(xscl);

  svg_line.append("g")
      .attr("transform", "translate(0," + (height + margin.top)  + ")")
      .call(xAxis);

  svg_line.append("g")
      .attr("transform", "translate(" + margin.left + ",0)")
      .call(yAxis);

  svg_line.append("text")             
      .attr("transform", "rotate(-90)")
      .attr("y", 0)
      .attr("x",0 - (height / 2) - margin.top)
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("sentiment");

  if (cent_min === "percent") {
      svg_line.append("text")             
        .attr("transform",
              "translate(" + (width/2 + margin.left) + " ," + 
                              (height + margin.top + 30) + ")")
        .style("text-anchor", "middle")
        .text("% of runtime");
  } else {
      svg_line.append("text")             
        .attr("transform",
              "translate(" + (width/2 + margin.left) + " ," + 
                              (height + margin.top + 30) + ")")
        .style("text-anchor", "middle")
        .text("minutes of runtime");
  }
};

// Checks if two films are selected for detail view. If true, then comparison data is requested 
// and displayed
function display_compare(side, film) {
  var comparison = false;

  if (side === "left") {
    compare_left_film = film;

    if (typeof compare_right_film !== "undefined") {
      if (compare_right_film.id === film.id) {
        return;
      } else {
        comparison = true;
      }
    }
  } else if (side === "right") {
    compare_right_film = film;

    if (typeof compare_left_film !== "undefined") {
      if (compare_left_film.id === film.id) {
        return;
      } else {
        comparison = true;
      }
    }
  }

  document.getElementsByClassName("comparebox")[0].style.display = 'inline';
  document.getElementById(side + "_film_title").innerText = film.title;
  document.getElementById(side + "_film_year").innerText = "(" + film.year + ")";
  document.getElementById(side + "_film_genres").innerText = "Genre: " + film.genres.join(", ");
  var zerofilled_id = ('000000'+film.id).slice(-7);
  var url = "https://www.imdb.com/title/tt" + zerofilled_id;
  document.getElementById(side + "_imdb_link").setAttribute('href', url);
  document.getElementById(side + "_imdb_link").innerText = 'on IMDb';

  $.ajax({url: "/get_detail_data/" + film.id, 
    type: 'POST',
    success:
      function(result){
        if (result === 'None') {
        } else {
          film_data = result;

          if (side === "left") {
            compare_left_film.speechtempo = film_data["speechtempo"];
            compare_left_film.sentiment = film_data["sentiment"];
            compare_left_film.stylometric_features = film_data["stylometric_features"];
          } else {
            compare_right_film.speechtempo = film_data["speechtempo"];
            compare_right_film.sentiment = film_data["sentiment"];
            compare_right_film.stylometric_features = film_data["stylometric_features"];
          }

          cloud = document.getElementById("tokens-cloud-" + side);
          generate_token_cloud(cloud, film_data["top_tokens"]);

          postags_table = document.getElementById("postags_table_" + side);
          generate_table(postags_table, film_data["top_postags"]);

          stopwords_table = document.getElementById("stopwords_table_" + side);
          generate_table(stopwords_table, film_data["top_stopwords"]);

          if (comparison === true) {
            display_comparison(compare_left_film, compare_right_film);
          }
          create_speechtempo_graph();
          create_sentiment_graph();
          generate_stylometric_table();
        }
    }
  })
};

// Display comparison data of Bag-of-Words model detail
function display_comparison(film_left, film_right) {
  $.ajax({url: "/get_compare_data/" + film_left.id + "/" + film_right.id, 
    type: 'POST',
    success:
    function(result){
      if (result === 'None') {
      } else {
        compare_data = result;
        cloud = document.getElementById("tokens-cloud-compare");
        generate_token_cloud(cloud, compare_data["tokens"]);
      }
  }
})
};