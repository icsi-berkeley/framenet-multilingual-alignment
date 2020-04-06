import * as d3 from 'd3';

var viz = { version: "1.1.8" };

viz.bP = function(){
	var keyPrimary, keySecondary, value
	,width, height, orient, barSize, min, pad
	,data, fill, g, edgeOpacity, duration
	,sortPrimary, sortSecondary, edgeMode
	;
	function bP(_){
	g=_;
			_.each(function() {
				var g = d3.select(this);
		var bars = bP.bars();
	
		var s = g.selectAll(".subBars")
				.data(bars.subBars)
				.enter()
		.append("g")
		.attr("transform", function(d){ return "translate("+d.x+","+d.y+")";})
				.attr("class","subBars")
				.append("rect")
				.attr("x",fx).attr("y",fy).attr("width",fw).attr("height",fh);
		
				if(typeof fill !=="undefined") s.style("fill", function(d){ return fill(d); });
			
				var e = g.selectAll(".edges")
				.data(bars.edges)
				.enter()
				.append("path")
				.attr("class","edges")
				.attr("d",function(d){ return d.path; })
		.style("fill-opacity",bP.edgeOpacity());
				
				if(typeof fill !=="undefined") e.style("fill", function(d){ return fill(d); });
		
				g.selectAll(".mainBars")
				.data(bars.mainBars)
				.enter()
		.append("g")
		.attr("transform", function(d){ return "translate("+d.x+","+d.y+")";})
				.attr("class","mainBars")
				.append("rect")
				.attr("x",fx).attr("y",fy).attr("width",fw).attr("height",fh)
		.style("fill-opacity",0)
		// .on("mouseover",bP.mouseover)
		// .on("mouseout",bP.mouseout);
	});
	}
	bP.data = function(_){
	if(!arguments.length) return data;
	data = _;
	return bP;
	}
	bP.fill = function(_){
	if(!arguments.length) return fill;
	fill = _;
	return bP;
	}
	bP.keyPrimary = function(_){ 
	if(!arguments.length) return typeof keyPrimary !== "undefined" ? keyPrimary : function(d){ return d[0]; } ;
	keyPrimary = _;
	return bP;		
	}
	bP.sortPrimary = function(_){ 
	if(!arguments.length) return typeof sortPrimary !== "undefined" ? sortPrimary : d3.ascending ;
	sortPrimary = _;
	return bP;		
	}
	bP.keySecondary = function(_){ 
	if(!arguments.length) return typeof keySecondary !== "undefined" ? keySecondary : function(d){ return d[1]; };
	keySecondary = _;
	return bP;		
	}
	bP.sortSecondary = function(_){ 
	if(!arguments.length) return typeof sortSecondary !== "undefined" ? sortSecondary : d3.ascending;
	sortSecondary = _;
	return bP;		
	}	  
	bP.value = function(_){ 
	if(!arguments.length) return typeof value !== "undefined" ? value : function(d){ return d[2]; };
	value = _;
	return bP;		
	}	  
	bP.width = function(_){
	if(!arguments.length) return typeof width !== "undefined" ? width : 400;
	width = _;
	return bP;
	}
	bP.height = function(_){
	if(!arguments.length) return typeof height !== "undefined" ? height : 600;
	height = _;
	return bP;
	}
	bP.barSize = function(_){
	if(!arguments.length) return typeof barSize !== "undefined" ? barSize : 35;
	barSize = _;
	return bP;
	}
	bP.min = function(_){
	if(!arguments.length) return typeof min !== "undefined" ? min : 0;
	min = _;
	return bP;
	}
	bP.orient = function(_){
	if(!arguments.length) return typeof orient !== "undefined" ? orient : "vertical";
	orient = _;
	return bP;
	}
	bP.pad = function(_){
	if(!arguments.length) return typeof pad !== "undefined" ? pad : 0;
	pad = _;
	return bP;
	}
	bP.duration = function(_){
	if(!arguments.length) return typeof duration !== "undefined" ? duration : 500;
	duration = _;
	return bP;
	}
	bP.edgeOpacity = function(_){
	if(!arguments.length) return typeof edgeOpacity !== "undefined" ? edgeOpacity : .4;
	edgeOpacity = _;
	return bP;
	}
	bP.edgeMode = function(_){
	if(!arguments.length) return typeof edgeMode !== "undefined" ? edgeMode : "curved";
	edgeMode = _;
	return bP;
	}
	bP.bars = function(mb){
	var mainBars={primary:[], secondary:[]};
	var subBars= {primary:[], secondary:[]};
	var key ={primary:bP.keyPrimary(), secondary:bP.keySecondary() };
	var _or = bP.orient();
	
	calculateMainBars("primary");
	calculateMainBars("secondary");	
	calculateSubBars("primary");	
	calculateSubBars("secondary");
	floorMainBars(); // ensure that main bars is atleast of size mi.n
	
	return {
			mainBars:mainBars.primary.concat(mainBars.secondary)
		,subBars:subBars.primary.concat(subBars.secondary)
		,edges:calculateEdges()
	};

	function isSelKey(d, part){ 
		return (typeof mb === "undefined" || mb.part === part) || (key[mb.part](d) === mb.key);
	}
	function floorMainBars(){
		var m =bP.min()/2;
		
		mainBars.primary.forEach(function(d){
			if(d.height<m) d.height=m;
		});
		mainBars.secondary.forEach(function(d){
			if(d.height<m) d.height=m;
		});
	}
	function calculateMainBars(part){
			;
		function v(d){ return isSelKey(d, part) ? bP.value()(d): 0;};

		var ps = d3.nest()
			.key(part==="primary"? bP.keyPrimary():bP.keySecondary())
			.sortKeys(part==="primary"? bP.sortPrimary():bP.sortSecondary())
			.rollup(function(d){ return d3.sum(d,v); })
			.entries(bP.data())
		;
		
		var bars = bpmap(ps, bP.pad(), bP.min(), 0, _or==="vertical" ? bP.height() : bP.width());
		var bsize = bP.barSize();
		ps.forEach(function(d,i){ 
			mainBars[part].push({
					x:_or==="horizontal"? (bars[i].s+bars[i].e)/2 : (part==="primary" ? bsize/2 : bP.width()-bsize/2)
				,y:_or==="vertical"? (bars[i].s+bars[i].e)/2 : (part==="primary" ? bsize/2 : bP.height()-bsize/2)
				,height:_or==="vertical"? (bars[i].e - bars[i].s)/2 : bsize/2
				,width: _or==="horizontal"? (bars[i].e - bars[i].s)/2 : bsize/2
				,part:part
				,key:d.key
				,value:d.value
				,percent:bars[i].p
			});
		});
	}
	function calculateSubBars(part){
		function v(d){ return isSelKey(d, part) ? bP.value()(d): 0;};
				
		var map = d3.map(mainBars[part], function(d){ return d.key});
		
		var ps = d3.nest()
			.key(part==="primary"? bP.keyPrimary():bP.keySecondary())
			.sortKeys(part==="primary"? bP.sortPrimary():bP.sortSecondary())
			.key(part==="secondary"? bP.keyPrimary():bP.keySecondary())
			.sortKeys(part==="secondary"? bP.sortPrimary():bP.sortSecondary())
			.rollup(function(d){ return d3.sum(d,v); })
			.entries(bP.data());

		ps.forEach(function(d){ 
			var g= map.get(d.key); 
			var bars = bpmap(d.values, 0, 0
					,_or==="vertical" ? g.y-g.height : g.x-g.width
					,_or==="vertical" ? g.y+g.height : g.x+g.width);

			var bsize = bP.barSize();			
			d.values.forEach(function(t,i){ 
				subBars[part].push({
						x:_or==="vertical"? part==="primary" ? bsize/2 : bP.width()-bsize/2 : (bars[i].s+bars[i].e)/2
					,y:_or==="horizontal"? part==="primary" ? bsize/2 : bP.height()-bsize/2 : (bars[i].s+bars[i].e)/2
					,height:(_or==="vertical"? bars[i].e - bars[i].s : bsize)/2
					,width: (_or==="horizontal"? bars[i].e - bars[i].s : bsize)/2
					,part:part
					,primary:part==="primary"? d.key : t.key
					,secondary:part==="primary"? t.key : d.key	
					,value:t.value
					,percent:bars[i].p*g.percent
					,index: part==="primary"? d.key+"|"+t.key : t.key+"|"+d.key //index 
				});
			});		  
		});
	}
	function calculateEdges(){	
		var map=d3.map(subBars.secondary,function(d){ return d.index;});
		var eMode= bP.edgeMode();
		
		return subBars.primary.map(function(d){
			var g=map.get(d.index);
			return {
					path:_or === "vertical" 
					? edgeVert(d.x+d.width,d.y+d.height,g.x-g.width,g.y+g.height,g.x-g.width,g.y-g.height,d.x+d.width,d.y-d.height)
					: edgeHoriz(d.x-d.width,d.y+d.height,g.x-g.width,g.y-g.height,g.x+g.width,g.y-g.height,d.x+d.width,d.y+d.height)
				,primary:d.primary
				,secondary:d.secondary
				,value:d.value
				,percent:d.percent
			}
		});
		function edgeVert(x1,y1,x2,y2,x3,y3,x4,y4){
			if(eMode==="straight") return ["M",x1,",",y1,"L",x2,",",y2,"L",x3,",",y3,"L",x4,",",y4,"z"].join("")
			var mx1=(x1+x2)/2,mx3=(x3+x4)/2;
			return ["M",x1,",",y1,"C",mx1,",",y1," ",mx1,",",y2,",",x2,",",y2,"L"
					,x3,",",y3,"C",mx3,",",y3," ",mx3,",",y4,",",x4,",",y4,"z"].join("");
		}
		function edgeHoriz(x1,y1,x2,y2,x3,y3,x4,y4){
			if(eMode==="straight") return ["M",x1,",",y1,"L",x2,",",y2,"L",x3,",",y3,"L",x4,",",y4,"z"].join("")
			var my1=(y1+y2)/2,my3=(y3+y4)/2;
			return ["M",x1,",",y1,"C",x1,",",my1," ",x2,",",my1,",",x2,",",y2,"L"
					,x3,",",y3,"C",x3,",",my3," ",x4,",",my3,",",x4,",",y4,"z"].join("");
		}
	}
	function bpmap(a/*array*/, p/*pad*/, m/*min*/, s/*start*/, e/*end*/){
		var r = m/(e-s-2*a.length*p); // cut-off for ratios
		var ln =0, lp=0, t=d3.sum(a,function(d){ return d.value;}); // left over count and percent.
		a.forEach(function(d){ if(d.value < r*t ){ ln+=1; lp+=d.value; }})
		var o= t < 1e-5 ? 0:(e-s-2*a.length*p-ln*m)/(t-lp); // scaling factor for percent.
		var b=s, ret=[];
		a.forEach(function(d){ 
			var v =d.value*o; 
			ret.push({
					s:b+p+(v<m?.5*(m-v): 0)
				,e:b+p+(v<m? .5*(m+v):v)
				,p:t < 1e-5? 0:d.value/t
			}); 
			b+=2*p+(v<m? m:v); 
		});
		
		return ret;
	}	  
	}	  
	bP.update = function(_data){
		data = _data;
	var b1 = bP.bars();
	var dur = bP.duration();
	
	g.selectAll(".subBars").data(b1.subBars).transition().duration(dur)
		.attr("transform", function(d){ return "translate("+d.x+","+d.y+")";})
				.select("rect")
				.attr("x",fx).attr("y",fy).attr("width",fw).attr("height",fh);
						
			g.selectAll(".edges").data(b1.edges).transition().duration(dur)
				.attr("d",function(d){ return d.path; })
		.style("fill-opacity",bP.edgeOpacity())
		.style("visibility", "visible")
					
			g.selectAll(".mainBars").data(b1.mainBars).transition().duration(dur)
		.attr("transform", function(d){ return "translate("+d.x+","+d.y+")";})
				.select("rect")
				.attr("x",fx).attr("y",fy).attr("width",fw).attr("height",fh)
		// .style("fill-opacity",0)
		.style("visibility", "hidden")
	}
	bP.mouseover = function(d){
		var newbars = bP.bars(d);
		g.selectAll(".mainBars").filter(function(r){ return r.part===d.part && r.key === d.key})
		.select("rect").style("stroke-opacity", 1);
		
		g.selectAll(".subBars").data(newbars.subBars)
		.transition().duration(bP.duration())
		.attr("transform", function(d){ return "translate("+d.x+","+d.y+")";})
		.select("rect").attr("x",fx).attr("y",fy).attr("width",fw).attr("height",fh);
		
		var e = g.selectAll(".edges")
		.data(newbars.edges);
		
		e.filter(function(t){ return t[d.part] === d.key;})
		.transition().duration(bP.duration())
		.style("fill-opacity",bP.edgeOpacity())
		.style("visibility", "visible")

		.attr("d",function(d){ return d.path});	
		
		e.filter(function(t){ return t[d.part] !== d.key;})
		.transition().duration(bP.duration())
		// .style("fill-opacity",0)
		.style("visibility", "hidden")
		.attr("d",function(d){ return d.path});	
		
		g.selectAll(".mainBars").data(newbars.mainBars)
		.transition().duration(bP.duration())
		.attr("transform", function(d){ return "translate("+d.x+","+d.y+")";})
		.select("rect").attr("x",fx).attr("y",fy).attr("width",fw).attr("height",fh)
	}
	bP.mouseout = function(d){
		var newbars = bP.bars();
					
		g.selectAll(".mainBars").filter(function(r){ return r.part===d.part && r.key === d.key})
		.select("rect").style("stroke-opacity", 0);
		
		g.selectAll(".subBars").data(newbars.subBars)
		.transition().duration(bP.duration())
		.attr("transform", function(d){ return "translate("+d.x+","+d.y+")";})
		.select("rect").attr("x",fx).attr("y",fy).attr("width",fw).attr("height",fh);
		
		g.selectAll(".edges").data(newbars.edges)
		.transition().duration(bP.duration())
		.style("fill-opacity",bP.edgeOpacity())
		.style("visibility", "visible")
		.attr("d",function(d){ return d.path});	
		
		g.selectAll(".mainBars").data(newbars.mainBars)
		.transition().duration(bP.duration())
		.attr("transform", function(d){ return "translate("+d.x+","+d.y+")";})
		.select("rect").attr("x",fx).attr("y",fy).attr("width",fw).attr("height",fh);
	}
	function fx(d){ return -d.width}
	function fy(d){ return -d.height}
		function fw(d){ return 2*d.width}
		function fh(d){ return 2*d.height}
	
	return bP;
}	

export default viz;
