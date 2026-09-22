/* RED ROCK — خونِ مرز — robust loader + fixed lock */
const $=s=>document.querySelector(s);
const clamp=(v,a,b)=>v<a?a:v>b?b:v, lerp=(a,b,t)=>a+(b-a)*t;
const rnd=(a,b)=>b===undefined?Math.random()*a:b+Math.random()*(a-b);
const TAU=Math.PI*2;
const smooth=(x,a,b)=>{x=clamp((x-a)/(b-a),0,1);return x*x*(3-2*x)};
const fa=n=>n.toLocaleString('fa-IR');

/* quality — works before THREE */
const QUAL={
 low:{seg:120,pix:0.8,shad:0,veg:0.5,dust:120,fog:0.62,stars:600},
 med:{seg:170,pix:1.1,shad:1024,veg:0.8,dust:240,fog:0.85,stars:1100},
 high:{seg:230,pix:1.45,shad:2048,veg:1,dust:400,fog:1,stars:1800}
};
const QNAME=['low','med','high'];
let qk=1, Q=QUAL.med;
let makeStars, buildTerrain, applyQuality;
applyQuality=function(){
  if(typeof renderer==='undefined'||!renderer) return;
  renderer.setPixelRatio(Math.min(devicePixelRatio,Q.pix));
  renderer.shadowMap.enabled=Q.shad>0;
  if(sun){ sun.castShadow=Q.shad>0; if(Q.shad>0){sun.shadow.mapSize.set(Q.shad,Q.shad); if(sun.shadow.map){sun.shadow.map.dispose();sun.shadow.map=null;}} }
  if(scene&&scene.fog){scene.fog.near=130*Q.fog; scene.fog.far=920*Q.fog;}
  if(makeStars) makeStars();
  if(buildTerrain) buildTerrain();
};
function setQ(k){qk=k;Q=QUAL[QNAME[k]];for(let i=0;i<3;i++){const b=$('#q'+i);if(b)b.classList.toggle('off',i!==k);} if(window.__gameInited) applyQuality();}
setQ(1);
$('#q0').onclick=()=>setQ(0); $('#q1').onclick=()=>setQ(1); $('#q2').onclick=()=>setQ(2);

/* THREE loader */
let THREE=null;
const THREE_URLS=[
 'https://unpkg.com/three@0.160.0/build/three.module.js',
 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js',
 'https://unpkg.com/three@0.160.0/build/three.module.min.js',
 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js',
 'https://esm.sh/three@0.160.0',
 'https://cdn.skypack.dev/three@0.160.0',
 'https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.js'
];
async function loadThree(){
  for(const u of THREE_URLS){
    try{
      const mod=await import(u);
      if(mod && (mod.Scene||mod.REVISION)) return mod;
    }catch(e){ console.warn('three fail',u); }
  }
  return null;
}

/* world math */
function h2(x,y){const n=Math.sin(x*127.1+y*311.7)*43758.5453123;return n-Math.floor(n);}
function vn(x,y){const xi=Math.floor(x),yi=Math.floor(y),xf=x-xi,yf=y-yi; const u=xf*xf*(3-2*xf),v=yf*yf*(3-2*yf); return lerp(lerp(h2(xi,yi),h2(xi+1,yi),u),lerp(h2(xi,yi+1),h2(xi+1,yi+1),u),v);}
function fbm(x,y,o){let s=0,a=.5,f=1;for(let i=0;i<(o||4);i++){s+=a*vn(x*f,y*f);f*=2;a*=.5;}return s;}
const SIZE=3000,HALF=SIZE/2,WATER=-5,TOWN={x:0,z:320},TOWNY=5,LAKE={x:-640,z:-380,r:150};
function heightAt(x,z){
  let h=(fbm(x*0.0026+11,z*0.0026-7,4)-0.5)*78;
  const m=fbm(x*0.00085+120,z*0.00085+40,3);
  h=lerp(h,h*0.16+52,smooth(m,0.47,0.62));
  h+=(fbm(x*0.004+3,z*0.004+9,2)-0.5)*9;
  const dl=Math.hypot(x-LAKE.x,z-LAKE.z), u=dl/LAKE.r;
  if(u<2.9){ const bowl=-18+40*smooth(u,0.5,1.5); h=lerp(h,bowl,1-smooth(u,1.6,2.9)); }
  const dt=Math.hypot(x-TOWN.x,z-TOWN.z);
  h=lerp(TOWNY,h,1-Math.exp(-(dt*dt)/(165*165)));
  return h;
}
const slopeAt=(x,z)=>{const e=3;return Math.hypot(heightAt(x+e,z)-heightAt(x-e,z),heightAt(x,z+e)-heightAt(x,z-e))/(2*e);};

/* globals filled after THREE */
let state='menu', dayT=0.28, last=performance.now(), frames=0, fpsT=0;
let renderer, scene, camera, hemi, sun, moon, starMesh, starMat, terrain, town;
let colliders=[], fires=[], TUM=[], BIRDS=[], enemies=[], LOOT=[], horses=[], TRC=[];
let P, WEPS, hero, cam, M, twGeo, twMat, dust, Pblood, Pdust, Pspark;
let AC=null,master=null,nbuf=null,windG=null;
let K={}, locked=false, firing=false, aiming=false;
let ddActive=false, ddTimer=0, ddCool=0;
let MISSIONS, mi=0, MS=null, prog=0, wp={x:0,z:0}, mt=0, wpMesh, wpRing;
let shoreR=LAKE.r, SHORE={x:0,z:0,y:0};
let elHUD, FEED=[], subT=0, toastT=0, hudT=0, howlT=8;
let _v1,_v2, wepBox, mmCtx, CAMPS;

function requestLock(){
  try{ const c=$('#c'); if(c&&c.requestPointerLock){ const r=c.requestPointerLock(); if(r&&r.catch) r.catch(()=>{}); } }catch(e){}
}

function buildWorld(){
  const canvas=$('#c');
  renderer=new THREE.WebGLRenderer({canvas,antialias:qk>0,powerPreference:'high-performance'});
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.shadowMap.enabled=Q.shad>0; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  scene=new THREE.Scene();
  scene.fog=new THREE.Fog(0xc8a37a,120*Q.fog,900*Q.fog);
  camera=new THREE.PerspectiveCamera(66,innerWidth/innerHeight,0.4,2600);
  function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h);renderer.setPixelRatio(Math.min(devicePixelRatio,Q.pix)); camera.aspect=w/h;camera.updateProjectionMatrix();}
  addEventListener('resize',resize); resize();
  _v1=new THREE.Vector3(); _v2=new THREE.Vector3();

  hemi=new THREE.HemisphereLight(0xbfd8ff,0x6b5537,0.85); scene.add(hemi);
  sun=new THREE.DirectionalLight(0xffe6bd,1.5); sun.castShadow=true;
  sun.shadow.mapSize.set(Q.shad||1024,Q.shad||1024);
  const sc=sun.shadow.camera; sc.left=-160;sc.right=160;sc.top=160;sc.bottom=-160;sc.near=1;sc.far=900;
  sun.shadow.bias=-0.0012; scene.add(sun); scene.add(sun.target);
  moon=new THREE.DirectionalLight(0x8fa8d8,0); scene.add(moon);

  makeStars=function(){
    if(starMesh){scene.remove(starMesh);starMesh.geometry.dispose();}
    const n=Q.stars,p=new Float32Array(n*3);
    for(let i=0;i<n;i++){const th=Math.random()*TAU,ph=Math.acos(rnd(1,0.02)),r=1900;
      p[i*3]=r*Math.sin(ph)*Math.cos(th);p[i*3+1]=Math.abs(r*Math.cos(ph))+40;p[i*3+2]=r*Math.sin(ph)*Math.sin(th);}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(p,3));
    starMat=new THREE.PointsMaterial({color:0xfff2d0,size:3.4,sizeAttenuation:false,transparent:true,opacity:0});
    starMesh=new THREE.Points(g,starMat);starMesh.frustumCulled=false;scene.add(starMesh);
  }; makeStars();

  for(let r=30;r<520;r+=2){
    let mn=1e9; for(let i=0;i<32;i++){const a=i/32*TAU;mn=Math.min(mn,heightAt(LAKE.x+Math.cos(a)*r,LAKE.z+Math.sin(a)*r));}
    if(mn>WATER+1.4){shoreR=Math.max(42,r-2);break;}
  }
  SHORE={x:LAKE.x+shoreR+52,z:LAKE.z+34}; SHORE.y=heightAt(SHORE.x,SHORE.z);

  buildTerrain=function(){
    if(terrain){scene.remove(terrain);terrain.geometry.dispose();terrain.material.dispose();}
    const S=Q.seg,g=new THREE.PlaneGeometry(SIZE,SIZE,S,S); g.rotateX(-Math.PI/2);
    const pos=g.attributes.position, col=new Float32Array(pos.count*3), c=new THREE.Color();
    const C={sand:0xb3894f,grass:0x8a8042,rock:0x7a5c46,red:0xa85c3c,wet:0x6f5c3e,peak:0xc9b48d};
    for(let i=0;i<pos.count;i++){
      const x=pos.getX(i),z=pos.getZ(i),y=heightAt(x,z); pos.setY(i,y);
      const sl=slopeAt(x,z), n=fbm(x*0.02,z*0.02,2); let base;
      if(y<WATER+2.5) base=C.wet; else if(sl>0.62) base=C.rock; else if(y>44) base=C.red; else if(n>0.56) base=C.grass; else base=C.sand;
      c.setHex(base); const v=0.86+n*0.32; if(y>60)c.lerp(new THREE.Color(C.peak),smooth(y,60,86));
      col[i*3]=c.r*v; col[i*3+1]=c.g*v; col[i*3+2]=c.b*v;
    }
    g.setAttribute('color',new THREE.BufferAttribute(col,3)); g.computeVertexNormals();
    const m=new THREE.MeshLambertMaterial({vertexColors:true});
    terrain=new THREE.Mesh(g,m); terrain.receiveShadow=true; scene.add(terrain);
    const wg=new THREE.CircleGeometry(shoreR,44); wg.rotateX(-Math.PI/2);
    const wm=new THREE.MeshPhongMaterial({color:0x2f5d63,transparent:true,opacity:0.82,shininess:90,specular:0x9fd6dd});
    const w=new THREE.Mesh(wg,wm); w.position.set(LAKE.x,WATER,LAKE.z); w.name='water';
    const old=scene.getObjectByName('water'); if(old)scene.remove(old); scene.add(w);
  }; buildTerrain();

  const lam=(hex,opt)=>new THREE.MeshLambertMaterial(Object.assign({color:hex},opt||{}));
  M={
   rock:lam(0x8a6a52,{flatShading:true}), rockD:lam(0x6b5040,{flatShading:true}),
   cac:lam(0x4c6f34), trunk:lam(0x5b4030), leaf:lam(0x47612e), leafD:lam(0x385025),
   wood:lam(0x8a6540), woodD:lam(0x5f4229), roof:lam(0x4a3324), metal:lam(0x6d6a63),
   metalD:lam(0x3b3833), cloth:lam(0xa8442f), clothB:lam(0x2f3d5c), skin:lam(0xd9a97c),
   dark:lam(0x241a12), gold:lam(0xe0a92c), blood:lam(0x8d1408), sand:lam(0xb08a55),
   hide:lam(0x6b4b34), glass:lam(0x9fc4c9,{transparent:true,opacity:0.5})
  };
  colliders=[]; fires=[]; TUM=[]; BIRDS=[]; enemies=[]; LOOT=[]; horses=[]; TRC=[];

  function inst(geo,mat,count,fn,cast){
    const im=new THREE.InstancedMesh(geo,mat,count), m=new THREE.Matrix4(), q=new THREE.Quaternion(), e=new THREE.Euler();
    let k=0;
    for(let i=0;i<count*3&&k<count;i++){
      const x=rnd(HALF-40,-HALF+40), z=rnd(HALF-40,-HALF+40);
      if(Math.hypot(x-TOWN.x,z-TOWN.z)<190) continue;
      if(Math.hypot(x-LAKE.x,z-LAKE.z)<shoreR+20) continue;
      const y=heightAt(x,z); if(y<WATER+3) continue;
      const r=fn?fn(x,y,z):{s:1,ry:rnd(TAU)}; if(!r) continue;
      e.set(r.rx||0,r.ry||0,r.rz||0); q.setFromEuler(e);
      m.compose(new THREE.Vector3(x,y+(r.oy||0),z),q,new THREE.Vector3(r.s,r.sy||r.s,r.s));
      im.setMatrixAt(k++,m);
    }
    im.count=k; im.castShadow=cast!==false; im.receiveShadow=true; im.instanceMatrix.needsUpdate=true;
    scene.add(im); return im;
  }
  const V=Q.veg;
  inst(new THREE.IcosahedronGeometry(1,0),M.rock,Math.floor(520*V),(x,y)=>({s:rnd(6,0.9),sy:rnd(4,0.6),ry:rnd(TAU),oy:-0.4}));
  inst(new THREE.IcosahedronGeometry(1,0),M.rockD,Math.floor(260*V),(x,y)=>({s:rnd(2.4,0.5),ry:rnd(TAU),oy:-0.2}));
  function merge(parts){
    let n=0; for(const p of parts) n+=(p.g.attributes.position?.count||1);
    const pos=new Float32Array(n*3), nor=new Float32Array(n*3), idx=[]; let vo=0;
    for(const p of parts){
      const g=p.g.clone(); if(p.m) g.applyMatrix4(p.m);
      const pa=g.attributes.position; if(pa){ pos.set(pa.array,vo*3); const na=g.attributes.normal; if(na) nor.set(na.array,vo*3); }
      const gi=g.index; if(gi&&gi.length){ for(let i=0;i<gi.length;i++) idx.push((gi[i]||0)+vo); } else if(g.index&&g.index.count){ for(let i=0;i<g.index.count;i++) idx.push(g.index.getX(i)+vo); }
      vo+=pa?pa.count:1; g.dispose&&g.dispose();
    }
    const o=new THREE.BufferGeometry(); o.setAttribute('position',new THREE.BufferAttribute(pos,3));
    o.setAttribute('normal',new THREE.BufferAttribute(nor,3)); if(idx.length) o.setIndex(idx); return o;
  }
  const TR=(x,y,z,rx,ry,rz)=>new THREE.Matrix4().compose(new THREE.Vector3(x,y,z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx||0,ry||0,rz||0)),new THREE.Vector3(1,1,1));
  const gCyl=(a,b,h,s)=>new THREE.CylinderGeometry(a,b,h,s||7);
  const cacGeo=merge([{g:gCyl(0.42,0.5,4.4),m:TR(0,2.2,0)},{g:gCyl(0.23,0.26,1.9,6),m:TR(0.62,2.5,0,0,0,-0.95)},{g:gCyl(0.23,0.26,2.3,6),m:TR(-0.66,2.9,0.2,0,0,0.95)},{g:gCyl(0.2,0.22,1.1,6),m:TR(1.16,3.1,0)},{g:gCyl(0.2,0.22,1.3,6),m:TR(-1.2,3.6,0.2)}]);
  inst(cacGeo,M.cac,Math.floor(320*V),(x,y)=>({s:rnd(1.5,0.7),ry:rnd(TAU)}));
  const treeGeo=merge([{g:gCyl(0.26,0.4,4.2,6),m:TR(0,2.1,0)},{g:new THREE.ConeGeometry(2.5,4.4,7),m:TR(0,5.4,0)},{g:new THREE.ConeGeometry(1.8,3.6,7),m:TR(0,7.8,0)}]);
  inst(treeGeo,M.leaf,Math.floor(200*V),(x,y)=>({s:rnd(1.5,0.75),ry:rnd(TAU)}));
  inst(merge([{g:new THREE.SphereGeometry(1.6,6,4),m:TR(0,1,0)},{g:new THREE.SphereGeometry(1.1,6,4),m:TR(1.1,0.8,0.4)}]), M.leafD,Math.floor(420*V),(x,y)=>({s:rnd(1.4,0.6),ry:rnd(TAU),sy:rnd(0.9,0.5)}),false);
  inst(new THREE.ConeGeometry(0.4,1.7,4),M.leaf,Math.floor(2600*V),(x,y)=>({s:rnd(1.5,0.6),ry:rnd(TAU)}),false);

  town=new THREE.Group(); scene.add(town);
  function box(w,h,d,mat,x,y,z,ry){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat); m.position.set(x,y,z); m.rotation.y=ry||0; m.castShadow=true; m.receiveShadow=true; return m;}
  function building(w,h,d,o){
    o=o||{}; const g=new THREE.Group();
    g.add(box(w,h,d,M.wood,0,h/2,0));
    const rl=w*0.62, over=0.7;
    g.add(box(rl,0.35,d+over*2,M.roof,-w*0.16,h+1.2,0,0.62));
    g.add(box(rl,0.35,d+over*2,M.roof, w*0.16,h+1.2,0,-0.62));
    if(o.front!==false){
      g.add(box(w*0.28,h*0.78,0.22,M.woodD,-w*0.2,h*0.39,d/2));
      g.add(box(w*0.24,h*0.3,0.16,M.glass, w*0.22,h*0.6,d/2));
      if(o.porch){
        g.add(box(w+2.6,0.22,3.2,M.woodD,0,h*0.72,d/2+1.6));
        for(const sx of [-1,1]) g.add(box(0.24,h*0.72,0.24,M.trunk,sx*(w/2+0.9),h*0.36,d/2+3));
        for(let i=0;i<4;i++) g.add(box(w+2.6,0.16,0.16,M.woodD,0,0.5+i*0.42,d/2+3.2));
      }
      if(o.sign){
        const s=box(w*0.86,1.1,0.18,M.dark,0,h*0.86,d/2+0.15); g.add(s);
        const c=document.createElement('canvas'); c.width=512;c.height=96;
        const cx=c.getContext('2d'); cx.fillStyle='#1a120a';cx.fillRect(0,0,512,96);
        cx.fillStyle='#d8a44b';cx.font='bold 54px Georgia';cx.textAlign='center';cx.fillText(o.sign,256,66);
        const tx=new THREE.CanvasTexture(c); tx.colorSpace=THREE.SRGBColorSpace;
        const sp=new THREE.Mesh(new THREE.PlaneGeometry(w*0.8,1.0),new THREE.MeshBasicMaterial({map:tx,transparent:true}));
        sp.position.set(0,h*0.86,d/2+0.26); g.add(sp);
      }
    }
    const x=o.x,z=o.z,ry=o.ry||0;
    g.position.set(x,heightAt(x,z),z); g.rotation.y=ry; town.add(g);
    colliders.push({x,z,hw:w/2+0.6,hd:d/2+0.6,ry,h:h+2}); return g;
  }
  building(14,7,11,{x:-26,z:296,ry:0,porch:1,sign:'SALOON'});
  building(12,6,10,{x: 4 ,z:294,ry:0,porch:1,sign:'BANK'});
  building(11,6,10,{x: 32,z:300,ry:0,porch:1,sign:'SHERIFF'});
  building(10,6,9 ,{x:-52,z:300,ry:0,sign:'STORE'});
  building(9,5.5,9,{x:-70,z:334,ry:1.5,sign:''});
  building(11,5.5,9,{x:-46,z:368,ry:3.14,porch:1,sign:''});
  building(9,5.5,8,{x:-14,z:372,ry:3.14,sign:''});
  building(12,5.5,9,{x: 20,z:374,ry:3.14,porch:1,sign:'HOTEL'});
  building(9,5.5,8,{x: 52,z:366,ry:-1.6,sign:''});
  building(13,5,11,{x: 74,z:330,ry:-1.6,sign:'STABLE'});
  building(7,9,7,{x:-88,z:296,ry:0.3,front:false});
  building(10,5,9,{x: 92,z:292,ry:-0.2,sign:''});
  (function(){const g=new THREE.Group();for(let i=0;i<4;i++){const a=i/4*TAU; g.add(box(0.4,7,0.4,M.trunk,Math.cos(a)*1.8,3.5,Math.sin(a)*1.8));} g.add(box(4.4,3.4,4.4,M.woodD,0,8.4,0)); town.add(g); const x=-6,z=250; g.position.set(x,heightAt(x,z),z); colliders.push({x,z,hw:2.6,hd:2.6,ry:0,h:11});})();
  function prop(geo,mat,x,z,ry,oy){const m=new THREE.Mesh(geo,mat); m.position.set(x,heightAt(x,z)+(oy||0),z); m.rotation.y=ry||0; m.castShadow=true;m.receiveShadow=true;town.add(m);return m;}
  const gBarrel=new THREE.CylinderGeometry(0.5,0.45,1.1,9), gCrate=new THREE.BoxGeometry(1.1,1.1,1.1);
  for(let i=0;i<26;i++){const x=rnd(90,-90),z=rnd(400,280);prop(i%2?gBarrel:gCrate,i%2?M.woodD:M.trunk,x,z,rnd(TAU),0.55);}
  for(let i=0;i<10;i++){const x=rnd(88,-88),z=rnd(402,278); prop(gBarrel,M.hide,x,z,0,0.05); prop(new THREE.CylinderGeometry(0.1,0.1,2.6,5),M.trunk,x+rnd(2,-2),z,0,1.3);}
  function campfire(x,z,scale){
    const g=new THREE.Group(); const s=scale||1;
    for(let i=0;i<6;i++){const a=i/6*TAU;const m=new THREE.Mesh(new THREE.CylinderGeometry(0.12,0.16,1.3,5),M.trunk); m.position.set(Math.cos(a)*0.4,0.5,Math.sin(a)*0.4); m.rotation.z=Math.cos(a)*0.5; m.rotation.x=-Math.sin(a)*0.5; m.castShadow=true; g.add(m);}
    const fl=new THREE.Mesh(new THREE.ConeGeometry(0.45*s,1.3*s,7),new THREE.MeshBasicMaterial({color:0xff9a2a,transparent:true,opacity:0.9})); fl.position.y=0.7*s; g.add(fl);
    const li=new THREE.PointLight(0xff8a2a,2.4,44,2); li.position.y=1.4; g.add(li);
    g.position.set(x,heightAt(x,z),z); scene.add(g); fires.push({g,fl,li,b:2.4,s}); return g;
  }
  campfire(28,332); campfire(-40,258); campfire(0,352);
  CAMPS=[{x:520,z:-260},{x:-540,z:640},{x:860,z:520},{x:-980,z:-180},{x:120,z:-780}];
  for(const c of CAMPS){
    campfire(c.x,c.z,1.4);
    for(let i=0;i<3;i++){const a=rnd(TAU), d=rnd(22,9), x=c.x+Math.cos(a)*d, z=c.z+Math.sin(a)*d; const t=new THREE.Mesh(new THREE.ConeGeometry(2.6,3.4,4),M.hide); t.position.set(x,heightAt(x,z)+1.7,z); t.rotation.y=rnd(TAU); t.castShadow=true; scene.add(t);}
    for(let i=0;i<5;i++){const x=c.x+rnd(16,-16),z=c.z+rnd(16,-16); const m=new THREE.Mesh(new THREE.CylinderGeometry(0.4,0.36,1,8),M.woodD); m.position.set(x,heightAt(x,z)+0.5,z); m.castShadow=true;m.receiveShadow=true;scene.add(m);}
  }

  twGeo=new THREE.IcosahedronGeometry(0.9,0); twMat=new THREE.MeshLambertMaterial({color:0x9a8148,wireframe:true});
  for(let i=0;i<Math.floor(46*Q.veg);i++){const m=new THREE.Mesh(twGeo,twMat); const x=rnd(HALF,-HALF),z=rnd(HALF,-HALF); m.position.set(x,heightAt(x,z)+0.9,z); m.scale.setScalar(rnd(1.5,0.6)); scene.add(m); TUM.push({m,vx:rnd(7,2),vz:rnd(4,-4),sp:rnd(2.4,0.8)});}
  const dN=Q.dust, dPos=new Float32Array(dN*3); for(let i=0;i<dN;i++){dPos[i*3]=rnd(60,-60);dPos[i*3+1]=rnd(6);dPos[i*3+2]=rnd(60,-60);}
  const dGeo=new THREE.BufferGeometry(); dGeo.setAttribute('position',new THREE.BufferAttribute(dPos,3));
  dust=new THREE.Points(dGeo,new THREE.PointsMaterial({color:0xcbb088,size:0.5,transparent:true,opacity:0.42,depthWrite:false})); dust.frustumCulled=false; scene.add(dust);
  for(let i=0;i<7;i++){const g=new THREE.Group(); for(const s of [-1,1]){const w=new THREE.Mesh(new THREE.BoxGeometry(1.6,0.08,0.4),M.dark);w.position.x=s*0.8;w.rotation.z=s*0.35;g.add(w);} g.scale.setScalar(rnd(1.1,0.6)); scene.add(g); BIRDS.push({g,a:rnd(TAU),r:rnd(220,60),y:rnd(120,55),sp:rnd(0.22,0.08),ph:rnd(TAU)});}

  function makeHuman(c){
    const g=new THREE.Group(), parts={};
    const matS=lam(c.shirt), matP=lam(c.pants), matH=lam(c.hat), matK=lam(c.skin||0xd9a97c);
    const hip=new THREE.Group(); hip.position.y=1.02; g.add(hip); parts.hip=hip;
    const torso=new THREE.Mesh(new THREE.BoxGeometry(0.66,0.74,0.36),matS); torso.position.y=0.37; torso.castShadow=true; hip.add(torso);
    if(c.poncho){const p=new THREE.Mesh(new THREE.ConeGeometry(0.72,1.0,4),lam(c.poncho)); p.position.y=0.42;p.rotation.y=Math.PI/4;p.castShadow=true;hip.add(p);}
    const belt=new THREE.Mesh(new THREE.BoxGeometry(0.7,0.12,0.4),M.dark); belt.position.y=0.06; hip.add(belt);
    const gun=new THREE.Mesh(new THREE.BoxGeometry(0.09,0.24,0.16),M.metalD); gun.position.set(0.3,-0.05,0.1); hip.add(gun);
    const mkArm=(sx)=>{const s=new THREE.Group(); s.position.set(sx*0.4,0.62,0); const a=new THREE.Mesh(new THREE.BoxGeometry(0.2,0.62,0.22),matS); a.position.y=-0.31; s.add(a); const hnd=new THREE.Mesh(new THREE.BoxGeometry(0.19,0.18,0.2),matK); hnd.position.y=-0.66; s.add(hnd); hip.add(s); return s;};
    parts.armL=mkArm(-1); parts.armR=mkArm(1);
    const mkLeg=(sx)=>{const s=new THREE.Group(); s.position.set(sx*0.19,0,0); const l=new THREE.Mesh(new THREE.BoxGeometry(0.26,1.0,0.28),matP); l.position.y=-0.5; s.add(l); const b=new THREE.Mesh(new THREE.BoxGeometry(0.27,0.22,0.44),M.dark); b.position.set(0,-1.0,0.07); s.add(b); hip.add(s); return s;};
    parts.legL=mkLeg(-1); parts.legR=mkLeg(1);
    const neck=new THREE.Mesh(new THREE.BoxGeometry(0.2,0.12,0.2),matK); neck.position.y=0.78; hip.add(neck);
    const head=new THREE.Group(); head.position.y=0.96; hip.add(head);
    const sk=new THREE.Mesh(new THREE.BoxGeometry(0.33,0.36,0.32),matK); sk.castShadow=true; head.add(sk);
    const brim=new THREE.Mesh(new THREE.CylinderGeometry(0.42,0.44,0.06,10),matH); brim.position.y=0.16; head.add(brim);
    const crown=new THREE.Mesh(new THREE.CylinderGeometry(0.2,0.22,0.24,10),matH); crown.position.y=0.28; head.add(crown);
    if(c.mask){const m=new THREE.Mesh(new THREE.BoxGeometry(0.35,0.18,0.34),lam(c.mask)); m.position.set(0,-0.06,0.01); head.add(m);}
    g.userData=parts; return g;
  }
  function animHuman(p,t,sp,aiming){
    const s=Math.min(sp/4,1), sw=s*Math.sin(t*9)*0.85;
    p.legL.rotation.x=sw; p.legR.rotation.x=-sw; p.armL.rotation.x=-sw*0.8; p.armR.rotation.x=sw*0.8;
    p.hip.position.y=1.02+Math.abs(Math.sin(t*9))*0.06*s;
    if(aiming){p.armL.rotation.x=-1.5;p.armR.rotation.x=-1.45;p.armR.rotation.z=-0.15;}
    else{p.armL.rotation.z=Math.sin(t*9)*0.06*s;p.armR.rotation.z=-Math.sin(t*9)*0.06*s;}
  }
  function makeHorse(col){
    const g=new THREE.Group(), b=lam(col), p={};
    const body=new THREE.Mesh(new THREE.BoxGeometry(0.95,1.05,2.5),b); body.position.y=1.62; body.castShadow=true; g.add(body);
    const chest=new THREE.Mesh(new THREE.BoxGeometry(0.85,0.8,0.7),b); chest.position.set(0,1.6,1.3); g.add(chest);
    const neck=new THREE.Mesh(new THREE.BoxGeometry(0.5,1.25,0.5),b); neck.position.set(0,2.25,1.6); neck.rotation.x=-0.55; neck.castShadow=true; g.add(neck);
    const hd=new THREE.Mesh(new THREE.BoxGeometry(0.42,0.44,0.85),b); hd.position.set(0,2.72,2.02); hd.rotation.x=-0.25; hd.castShadow=true; g.add(hd);
    const mane=new THREE.Mesh(new THREE.BoxGeometry(0.16,1.0,0.4),M.dark); mane.position.set(0,2.42,1.5); mane.rotation.x=-0.6; g.add(mane);
    const tail=new THREE.Group(); tail.position.set(0,1.9,-1.25); g.add(tail); p.tail=tail;
    const tl=new THREE.Mesh(new THREE.BoxGeometry(0.16,1.3,0.16),M.dark); tl.position.y=-0.6; tl.rotation.x=0.35; tail.add(tl);
    const mkLeg=(x,z,ph)=>{const s=new THREE.Group(); s.position.set(x,1.5,z); const up=new THREE.Mesh(new THREE.BoxGeometry(0.24,0.85,0.26),b); up.position.y=-0.42; up.castShadow=true; s.add(up); const lo=new THREE.Group(); lo.position.y=-0.85; s.add(lo); const l2=new THREE.Mesh(new THREE.BoxGeometry(0.2,0.7,0.22),b); l2.position.y=-0.35; lo.add(l2); const hf=new THREE.Mesh(new THREE.BoxGeometry(0.24,0.16,0.3),M.dark); hf.position.set(0,-0.72,0.04); lo.add(hf); g.add(s); return {s,lo,ph};};
    p.legs=[mkLeg(-0.32,0.95,0),mkLeg(0.32,0.95,Math.PI),mkLeg(-0.32,-0.95,Math.PI),mkLeg(0.32,-0.95,0)];
    const saddle=new THREE.Mesh(new THREE.BoxGeometry(0.95,0.2,1.0),M.hide); saddle.position.set(0,2.22,0.1); g.add(saddle);
    const stp=new THREE.Mesh(new THREE.BoxGeometry(0.3,0.3,0.5),M.woodD); stp.position.set(0,2.32,0.15); g.add(stp);
    g.userData=p; return g;
  }
  function animHorse(p,t,sp){ const s=Math.min(sp/12,1); for(const L of p.legs){const a=Math.sin(t*11+L.ph)*0.9*s; L.s.rotation.x=a; L.lo.rotation.x=Math.max(0,-a)*1.5+ (s>0.5?-0.4*s:0);} p.tail.rotation.x=0.2+Math.sin(t*5)*0.12*s; }

  P={pos:new THREE.Vector3(TOWN.x,0,TOWN.z+18), vel:new THREE.Vector3(), yaw:0, hp:100,maxHp:100,st:100,dd:100,money:40,bounty:0,kills:0,dead:false, wep:0,mag:[6,0],res:[42,0],crouch:false,mounted:null,grounded:true,vY:0,t:0,cd:0,reload:0};
  WEPS=[{n:'هفت‌تیر',k:'REVOLVER',dmg:36,mag:6,spread:0.016,rate:0.36,rld:1.45,auto:false},{n:'تفنگ تکراری',k:'REPEATER',dmg:74,mag:8,spread:0.005,rate:0.62,rld:2.1,auto:true}];
  hero=makeHuman({shirt:0x8a3a26,pants:0x3b3a44,hat:0x54381f,poncho:0x6e4a2c}); scene.add(hero);
  cam={yaw:0,pitch:-0.12,dist:5.4,tdist:5.4,recoil:0,shake:0};
  function addHorse(x,z,wild,col){const h=makeHorse(col||0x6b4a30); h.position.set(x,heightAt(x,z),z); scene.add(h); const o={m:h,x,z,yaw:rnd(TAU),wild:!!wild,sp:0,t:rnd(9),wp:null}; horses.push(o); return o;}
  addHorse(TOWN.x+76,TOWN.z+14,false,0x4a3423); addHorse(SHORE.x,SHORE.z,true,0xd8cbb0);
  for(const c of CAMPS) addHorse(c.x+rnd(18,-18),c.z+rnd(18,-18),false,0x5c4433);

  /* input */
  let mmVisible=true, wpVisible=true;
  addEventListener('keydown',e=>{
    K[e.code]=true;
    if(e.code==='Escape'){ if(state==='play') pause(); else if(state==='pause') $('#resume').click(); }
    if(e.code==='KeyM'){ mmVisible=!mmVisible; const w=$('#mmw'); if(w) w.classList.toggle('hid',!mmVisible); }
    if(e.code==='KeyH'){ wpVisible=!wpVisible; if(wpMesh) wpMesh.visible=wpVisible&&!!MS; if(wpRing) wpRing.visible=wpVisible&&!!MS; }
    if(state!=='play') return;
    if(e.code==='KeyR') startReload();
    if(e.code==='KeyQ') deadEye();
    if(e.code==='KeyE') toggleMount();
    if(e.code==='Digit1') P.wep=0;
    if(e.code==='Digit2'&&P.res[1]>0) P.wep=1;
  });
  addEventListener('keyup',e=>K[e.code]=false);
  canvas.addEventListener('click',()=>{ if(state==='play'&&!locked) requestLock(); });
  document.addEventListener('pointerlockchange',()=>{locked=document.pointerLockElement===canvas; if(!locked&&state==='play') pause();});
  addEventListener('mousemove',e=>{ if(!locked||state!=='play')return; cam.yaw-=e.movementX*0.0022; cam.pitch=clamp(cam.pitch+e.movementY*0.0020,-0.5,0.95);});
  addEventListener('mousedown',e=>{ if(state!=='play')return; if(e.button===0)firing=true; if(e.button===2){aiming=true;cam.tdist=2.6;} });
  addEventListener('mouseup',e=>{ if(e.button===0)firing=false; if(e.button===2){aiming=false;cam.tdist=5.4;} });
  addEventListener('contextmenu',e=>e.preventDefault());

  function Particles(hex,count,size,grav){
    const p=new Float32Array(count*3), v=new Float32Array(count*3), l=new Float32Array(count);
    const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.BufferAttribute(p,3));
    const m=new THREE.PointsMaterial({color:hex,size,transparent:true,opacity:0.95,depthWrite:false});
    const pts=new THREE.Points(g,m); pts.frustumCulled=false; scene.add(pts); let cur=0;
    return {pts,p,v,l,g,spawn(x,y,z,n,sp,up,life){for(let i=0;i<n;i++){const k=(cur++)%count; p[k*3]=x;p[k*3+1]=y;p[k*3+2]=z; v[k*3]=rnd(sp,-sp);v[k*3+1]=rnd(up,0.2);v[k*3+2]=rnd(sp,-sp); l[k]=life*(0.6+Math.random()*0.6);} g.attributes.position.needsUpdate=true;}, update(dt){for(let i=0;i<count;i++){if(l[i]<=0)continue;l[i]-=dt; v[i*3+1]-=grav*dt; p[i*3]+=v[i*3]*dt;p[i*3+1]+=v[i*3+1]*dt;p[i*3+2]+=v[i*3+2]*dt; if(l[i]<=0)p[i*3+1]=-999;} g.attributes.position.needsUpdate=true;}};
  }
  Pblood=Particles(0x9d1408,220,0.22,14); Pdust=Particles(0xc2a377,260,0.34,7); Pspark=Particles(0xffc46a,160,0.16,9);
  for(let i=0;i<20;i++){const g=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(),new THREE.Vector3()]); const l=new THREE.Line(g,new THREE.LineBasicMaterial({color:0xffe0a0,transparent:true,opacity:0})); l.frustumCulled=false; scene.add(l); TRC.push({l,g,t:0});}
  function tracer(a,b){for(const t of TRC){if(t.t<=0){t.t=0.09; t.g.attributes.position.setXYZ(0,a.x,a.y,a.z);t.g.attributes.position.setXYZ(1,b.x,b.y,b.z); t.g.attributes.position.needsUpdate=true; t.l.material.opacity=0.85; return;}}}
  function updateTracers(dt){for(const t of TRC){if(t.t>0){t.t-=dt;t.l.material.opacity=Math.max(0,t.t/0.09)*0.85;}}}

  function audioInit(){
    if(AC) return; try{
      AC=new (window.AudioContext||window.webkitAudioContext)();
      master=AC.createGain(); master.gain.value=0.55; master.connect(AC.destination);
      nbuf=AC.createBuffer(1,AC.sampleRate*2,AC.sampleRate);
      const d=nbuf.getChannelData(0); for(let i=0;i<d.length;i++) d[i]=Math.random()*2-1;
      const src=AC.createBufferSource(); src.buffer=nbuf; src.loop=true;
      const f=AC.createBiquadFilter(); f.type='lowpass'; f.frequency.value=340;
      windG=AC.createGain(); windG.gain.value=0.05;
      src.connect(f); f.connect(windG); windG.connect(master); src.start();
      const lfo=AC.createOscillator(); lfo.frequency.value=0.07; const lg=AC.createGain(); lg.gain.value=0.035; lfo.connect(lg); lg.connect(windG.gain); lfo.start();
    }catch(e){}
  }
  function burst(dur,f0,f1,vol,type){ if(!AC)return; const t=AC.currentTime; const s=AC.createBufferSource(); s.buffer=nbuf; s.playbackRate.value=rnd(1.4,0.8); const f=AC.createBiquadFilter(); f.type=type||'lowpass'; f.frequency.setValueAtTime(f0,t); f.frequency.exponentialRampToValueAtTime(Math.max(40,f1),t+dur); const g=AC.createGain(); g.gain.setValueAtTime(vol,t); g.gain.exponentialRampToValueAtTime(0.0001,t+dur); s.connect(f); f.connect(g); g.connect(master); s.start(t); s.stop(t+dur+0.02); }
  function tone(fr,dur,vol,type,slide){ if(!AC)return; const t=AC.currentTime, o=AC.createOscillator(), g=AC.createGain(); o.type=type||'sine'; o.frequency.setValueAtTime(fr,t); if(slide) o.frequency.exponentialRampToValueAtTime(Math.max(30,slide),t+dur); g.gain.setValueAtTime(0.0001,t); g.gain.exponentialRampToValueAtTime(vol,t+0.01); g.gain.exponentialRampToValueAtTime(0.0001,t+dur); o.connect(g); g.connect(master); o.start(t); o.stop(t+dur+0.02); }
  const sfx={shot:()=>{burst(0.24,2600,180,0.55);tone(150,0.16,0.3,'square',60);}, rifle:()=>{burst(0.36,3600,150,0.7);tone(110,0.24,0.35,'square',45);}, eshot:()=>{burst(0.2,1400,140,0.22);}, click:()=>{tone(1400,0.05,0.16,'square',700);}, reload:()=>{tone(700,0.09,0.14,'square',320);setTimeout(()=>tone(520,0.1,0.13,'square',260),220);}, hit:()=>{burst(0.12,900,120,0.3,'bandpass');}, hurt:()=>{burst(0.3,500,80,0.4);tone(90,0.3,0.25,'sawtooth',50);}, death:()=>{tone(200,0.6,0.22,'sawtooth',60);}, hoof:()=>{burst(0.09,420,90,0.22,'bandpass');}, neigh:()=>{tone(520,0.5,0.2,'sawtooth',240);setTimeout(()=>tone(420,0.4,0.16,'sawtooth',180),180);}, howl:()=>{tone(420,1.4,0.12,'sine',300);setTimeout(()=>tone(330,1.6,0.1,'sine',180),500);}, coin:()=>{tone(1200,0.1,0.18,'triangle',1800);setTimeout(()=>tone(1600,0.12,0.14,'triangle',2100),90);}, heal:()=>{tone(600,0.2,0.14,'sine',900);}, dd:()=>{tone(180,1.2,0.2,'sine',900);burst(0.8,400,3000,0.15,'bandpass');}};

  const KIND={bandit:{hp:62,sp:4.2,dmg:9,acc:0.42,col:0x6b3a2a,hat:0x2c2620,pay:25,name:'راهزن'}, gunman:{hp:100,sp:4.8,dmg:13,acc:0.55,col:0x2f3a4a,hat:0x1e1a16,pay:45,name:'تفنگ‌دار'}, boss:{hp:520,sp:4.4,dmg:19,acc:0.7,col:0x4a1f1f,hat:0x121212,pay:400,name:'کلانترِ خائن'}};
  function spawnEnemy(x,z,kind,alert){
    const k=KIND[kind]||KIND.bandit; const m=makeHuman({shirt:k.col,pants:0x2e2a24,hat:k.hat,mask:0x8a7a5a});
    m.position.set(x,heightAt(x,z),z); scene.add(m);
    const e={m,x,z,hp:k.hp,max:k.hp,sp:k.sp,k,kind,state:alert?'alert':'idle',t:rnd(9),ph:rnd(TAU),aim:rnd(2,0.5),alert:!!alert,dead:false,vy:0,flash:0,homeX:x,homeZ:z,wp:rnd(TAU)};
    enemies.push(e); return e;
  }
  function mkLoot(x,z,type){
    const geo={ammo:new THREE.BoxGeometry(0.7,0.35,0.5),gold:new THREE.BoxGeometry(0.5,0.3,0.8),health:new THREE.BoxGeometry(0.5,0.35,0.5)}[type];
    const mat={ammo:M.metalD,gold:M.gold,health:lam(0xd8d8d0)}[type];
    const m=new THREE.Mesh(geo,mat); const y=heightAt(x,z)+0.6; m.position.set(x,y,z); m.castShadow=true; scene.add(m);
    const o={m,x,z,y,type,t:rnd(9),dead:false}; LOOT.push(o); return o;
  }
  function killEnemy(e,byPlayer){
    e.dead=true; e.m.rotation.z=Math.PI/2*rnd(1,-1); e.m.position.y+=0.2;
    if(byPlayer){ P.kills++; P.money+=e.k.pay; P.bounty++; sfx.death(); feed(e.k.name+' کشته شد  +$'+fa(e.k.pay)); mkLoot(e.x,e.z,Math.random()<0.55?'ammo':'gold'); if(P.bounty>=5&&P.bounty%5===0) bountyHunters(); }
  }
  function bountyHunters(){
    let alive=0; for(const ee of enemies) if(!ee.dead) alive++; if(alive>12) return;
    feed('★ جایزه‌بگیرها دنبالِ تو افتادند!');
    for(let i=0;i<3;i++){const a=rnd(TAU),d=rnd(70,45); spawnEnemy(clamp(P.pos.x+Math.cos(a)*d,-HALF+50,HALF-50),clamp(P.pos.z+Math.sin(a)*d,-HALF+50,HALF-50),'gunman',true);}
    toast('جایزه‌بگیر','سه شکارچی در راه‌اند','$'+fa(P.bounty*10));
  }

  const tmpV=new THREE.Vector3();
  function playerShoot(){
    const w=WEPS[P.wep]; if(P.reload>0||P.cd>0) return; if(P.mag[P.wep]<=0){sfx.click(); startReload(); return;}
    P.mag[P.wep]--; P.cd=w.rate*(ddActive?0.55:1); cam.recoil+=0.06; cam.shake+=0.35; if(P.wep) sfx.rifle(); else sfx.shot();
    const o=new THREE.Vector3(), dir=new THREE.Vector3(); camera.getWorldPosition(o); camera.getWorldDirection(dir);
    const sp=w.spread*(aiming?0.35:1)*(P.mounted?2.2:1); dir.x+=rnd(sp,-sp); dir.y+=rnd(sp,-sp); dir.z+=rnd(sp,-sp); dir.normalize();
    Pspark.spawn(o.x+dir.x*1.2,o.y+dir.y*1.2-0.1,o.z+dir.z*1.2,5,1.4,1.2,0.18);
    let best=null,bt=1e9;
    for(const e of enemies){ if(e.dead) continue; const cx=e.x-o.x, cy=(e.m.position.y+1.2)-o.y, cz=e.z-o.z; const along=cx*dir.x+cy*dir.y+cz*dir.z; if(along<0.5||along>400) continue; const px=cx-dir.x*along, py=cy-dir.y*along, pz=cz-dir.z*along; const d2=px*px+py*py+pz*pz; if(d2<1.1&&along<bt){bt=along;best=e;} }
    if(best){ const hx=o.x+dir.x*bt, hy=o.y+dir.y*bt, hz=o.z+dir.z*bt; tracer(o, tmpV.set(hx,hy,hz)); const dmg=w.dmg*(ddActive?1.6:1); best.hp-=dmg; best.flash=0.16; best.alert=true; best.state='chase'; Pblood.spawn(hx,hy,hz,12,2.6,2.2,0.7); sfx.hit(); if(best.hp<=0) killEnemy(best,true); }
    else { const hx=o.x+dir.x*260, hy=o.y+dir.y*260, hz=o.z+dir.z*260; tracer(o,tmpV.set(hx,hy,hz)); const gy=heightAt(hx,hz); if(Math.abs(gy-hy)<60) Pdust.spawn(hx,gy+0.3,hz,8,1.2,2,0.6); }
    for(const e of enemies) if(!e.dead&&Math.hypot(e.x-P.pos.x,e.z-P.pos.z)<110){e.alert=true;if(e.state==='idle')e.state='alert';}
  }
  function startReload(){ const w=WEPS[P.wep]; if(P.reload>0||P.mag[P.wep]>=w.mag||P.res[P.wep]<=0||P.mounted) return; P.reload=w.rld; sfx.reload(); }
  function finishReload(){ const w=WEPS[P.wep], need=w.mag-P.mag[P.wep], take=Math.min(need,P.res[P.wep]); P.mag[P.wep]+=take; P.res[P.wep]-=take; }
  function deadEye(){ if(ddActive||ddCool>0||P.dd<25) return; ddActive=true; ddTimer=5; P.dd-=45; sfx.dd(); feed('☠ دد آی فعال شد'); }

  MISSIONS=[
   {t:'راهزنی در گذرگاه',d:'کمپِ راهزن‌ها را پاک کن',type:'kill',need:6,zone:CAMPS[0],pay:150,intro:'یه کمپِ راهزن شرقِ شهر زده‌اند. شش نفرند. تفنگت را روغن بزن.'},
   {t:'اسبِ وحشی',d:'اسبِ سفیدِ کنارِ دریاچه را بگیر',type:'horse',need:1,zone:{x:SHORE.x,z:SHORE.z},pay:140,intro:'کنارِ دریاچه یک اسبِ سفیدِ وحشی دیده‌اند. زین ندارد، ولی طلا دارد.'},
   {t:'کاروانِ طلا',d:'سه صندوقِ طلا از کاروان بردار',type:'collect',need:3,zone:CAMPS[2],pay:300,intro:'کاروانِ طلا در کوهپایه اردو زده. سه صندوق بردار و در برو.'},
   {t:'دوئل با کلانترِ خائن',d:'کلانترِ فاسد را بکش',type:'boss',need:1,zone:CAMPS[3],pay:600,intro:'کلانتر خودش با راهزن‌ها معامله می‌کرد. وقتِ حساب‌رسی است.'},
   {t:'سوار به سمتِ مکزیک',d:'به مرزِ جنوب برس',type:'reach',need:1,zone:{x:60,z:1380},pay:900,intro:'همه دنبالِ تویند. فقط برو جنوب، تا مرز. پشتِ سرت را نگاه نکن.'}
  ];
  wpMesh=new THREE.Mesh(new THREE.CylinderGeometry(0.7,0.7,24,8,1,true), new THREE.MeshBasicMaterial({color:0xe8b45c,transparent:true,opacity:0.06,side:THREE.DoubleSide,depthWrite:false})); wpMesh.frustumCulled=false; scene.add(wpMesh);
  wpRing=new THREE.Mesh(new THREE.TorusGeometry(1.2,0.08,5,12),new THREE.MeshBasicMaterial({color:0xe8b45c,transparent:true,opacity:0.40})); wpRing.rotation.x=Math.PI/2; scene.add(wpRing);
  function startMission(i){ mi=i; MS=MISSIONS[i]; prog=0; mt=0; wp.x=MS.zone.x; wp.z=MS.zone.z; const y=heightAt(wp.x,wp.z); wpMesh.position.set(wp.x,y+12,wp.z); wpRing.position.set(wp.x,y+0.18,wp.z); wpMesh.visible=wpRing.visible=wpVisible; toast('مأموریت',MS.t,'$'+fa(MS.pay)); subtitle(MS.intro,7); if(MS.type==='kill'){for(let k=0;k<MS.need;k++)spawnEnemy(wp.x+rnd(26,-26),wp.z+rnd(26,-26),'bandit',false);} if(MS.type==='boss'){spawnEnemy(wp.x,wp.z,'boss',true); for(let k=0;k<4;k++)spawnEnemy(wp.x+rnd(30,-30),wp.z+rnd(30,-30),'gunman',false);} if(MS.type==='collect'){for(let k=0;k<3;k++)mkLoot(wp.x+rnd(22,-22),wp.z+rnd(22,-22),'gold'); for(let k=0;k<5;k++)spawnEnemy(wp.x+rnd(34,-34),wp.z+rnd(34,-34),'gunman',false);} if(MS.type==='reach'){for(let k=0;k<6;k++)spawnEnemy(P.pos.x+rnd(90,-90),P.pos.z+rnd(90,-90),'gunman',true);} }
  function objProgress(n){ if(!MS||state!=='play')return; prog+=n; if(prog>=MS.need) completeMission(); }
  function completeMission(){ P.money+=MS.pay; sfx.coin(); if(mi===1){P.res[1]+=24;feed('تفنگِ تکراری گرفتی — کلید <kbd>2</kbd>');} toast('مأموریت تمام شد',MS.t,'+$'+fa(MS.pay)); MS=null; setTimeout(()=>{ if(mi+1<MISSIONS.length) startMission(mi+1); else {toast('پایان','به مکزیک رسیدی','کلِ پول: $'+fa(P.money)); MS=null;} },4200); }

  elHUD={hp:$('#hpB>i'),st:$('#stB>i'),dd:$('#ddB>i'),mon:$('#mon'),bty:$('#bty'),stars:$('#stars'), objd:$('#obj .d'),objp:$('#obj .p'),hint:$('#hint'),sub:$('#sub'),feed:$('#feed'),toast:$('#toast'), ta:$('#toast .b'),tc:$('#toast .c'),fps:$('#fps')};
  FEED=[]; function feed(t){FEED.unshift({t,a:1});if(FEED.length>4)FEED.pop();}
  function subtitle(t,s){elHUD.sub.textContent=t;elHUD.sub.classList.remove('hid');subT=s;}
  function toast(a,b,c){elHUD.toast.querySelector('.a').textContent=a;elHUD.ta.textContent=b;elHUD.tc.textContent=c||''; elHUD.toast.classList.remove('hid');toastT=3.6;}
  wepBox=document.createElement('div'); wepBox.id='wep'; wepBox.innerHTML='<div class="n"></div><div class="a"></div>'; $('#hud').appendChild(wepBox);
  mmCtx=$('#mm').getContext('2d');
  function drawHUD(){
    elHUD.hp.style.width=(P.hp/P.maxHp*100)+'%'; elHUD.st.style.width=P.st+'%'; elHUD.dd.style.width=P.dd+'%';
    elHUD.mon.textContent='$'+fa(Math.floor(P.money)); elHUD.bty.textContent='جایزه: '+fa(P.bounty);
    const lv=clamp(Math.floor(P.bounty/3),0,5); elHUD.stars.innerHTML='◈◈◈◈◈'.split('').map((s,i)=>i<lv?'<i>◈</i>':'◈').join('');
    const w=WEPS[P.wep]; wepBox.querySelector('.n').textContent=w.k; wepBox.querySelector('.a').innerHTML=(P.reload>0?'<span style="font-size:22px">پر کردن…</span>':fa(P.mag[P.wep])+'<s>/'+fa(P.res[P.wep])+'</s>');
    if(MS){elHUD.objd.textContent=MS.d; const dd=Math.hypot(wp.x-P.pos.x,wp.z-P.pos.z); elHUD.objp.textContent=(MS.type==='kill'||MS.type==='collect'?fa(Math.min(prog,MS.need))+' / '+fa(MS.need)+'  ·  ':'')+fa(Math.round(dd))+' متر';}
    else {elHUD.objd.textContent='آزاد — شهر در اختیارِ توست';elHUD.objp.textContent='';}
    elHUD.feed.innerHTML=FEED.map(f=>'<div style="opacity:'+f.a.toFixed(2)+'">'+f.t+'</div>').join('');
  }
  function drawMap(){
    const S=mmCtx.canvas.width||96,R=S/2,SC=R/500;
    mmCtx.clearRect(0,0,S,S);
    mmCtx.fillStyle='#1a1208'; mmCtx.beginPath(); mmCtx.arc(R,R,R,0,TAU); mmCtx.fill();
    mmCtx.save(); mmCtx.beginPath(); mmCtx.arc(R,R,R-0.5,0,TAU); mmCtx.clip();
    const px=P.pos.x,pz=P.pos.z; const put=(x,z)=>[(x-px)*SC+R,(z-pz)*SC+R];
    let a=put(LAKE.x,LAKE.z);
    mmCtx.fillStyle='rgba(44,85,96,0.55)'; mmCtx.beginPath(); mmCtx.arc(a[0],a[1],Math.max(1.2,shoreR*SC*0.32),0,TAU); mmCtx.fill();
    for(const c of CAMPS){ a=put(c.x,c.z); if(Math.hypot(a[0]-R,a[1]-R)>R+2) continue; mmCtx.fillStyle='#5a3a1e'; mmCtx.beginPath(); mmCtx.arc(a[0],a[1],0.7,0,TAU); mmCtx.fill(); }
    mmCtx.fillStyle='#4a3620'; a=put(TOWN.x,TOWN.z); mmCtx.fillRect(a[0]-1.5,a[1]-1.5,3,3);
    for(const l of LOOT){ if(l.dead) continue; a=put(l.x,l.z); if(Math.hypot(a[0]-R,a[1]-R)>R) continue; mmCtx.fillStyle='#e8b45c'; mmCtx.fillRect(a[0]-0.5,a[1]-0.5,1,1); }
    for(const h of horses){ a=put(h.x,h.z); if(Math.hypot(a[0]-R,a[1]-R)>R) continue; mmCtx.fillStyle=h.wild?'#f0e6cc':'#8a6a45'; mmCtx.beginPath(); mmCtx.arc(a[0],a[1],0.8,0,TAU); mmCtx.fill(); }
    for(const e of enemies){ if(e.dead) continue; const d=Math.hypot(e.x-px,e.z-pz); if(d>260) continue; a=put(e.x,e.z); mmCtx.fillStyle=e.kind==='boss'?'#ff3a20':'#c0392b'; mmCtx.beginPath(); mmCtx.arc(a[0],a[1],e.kind==='boss'?1.4:0.7,0,TAU); mmCtx.fill(); }
    if(MS){
      a=put(wp.x,wp.z); let ax=a[0], ay=a[1]; const d=Math.hypot(a[0]-R,a[1]-R); if(d>R-3){ const k=(R-3)/d; ax=R+(a[0]-R)*k; ay=R+(a[1]-R)*k; }
      mmCtx.fillStyle='#f0c050'; mmCtx.beginPath(); mmCtx.arc(ax,ay,1.6,0,TAU); mmCtx.fill();
    }
    mmCtx.restore();
    mmCtx.save(); mmCtx.translate(R,R); mmCtx.rotate(-cam.yaw);
    mmCtx.fillStyle='#f2e2b8'; mmCtx.beginPath(); mmCtx.moveTo(0,-3); mmCtx.lineTo(1.4,2); mmCtx.lineTo(0,1); mmCtx.lineTo(-1.4,2); mmCtx.closePath(); mmCtx.fill();
    mmCtx.restore();
  }
  function damagePlayer(d){ P.hp-=d; $('#hurt').style.opacity=clamp(d/26,0.25,1); cam.shake+=0.3; sfx.hurt(); setTimeout(()=>$('#hurt').style.opacity=0,120); if(P.hp<=0) die(); }
  function die(){ if(P.dead)return; P.dead=true; state='over'; document.exitPointerLock&&document.exitPointerLock(); $('#ostat').textContent='کشته‌ها: '+fa(P.kills)+'  ·  پول: $'+fa(P.money)+'  ·  مأموریت: '+fa(mi+1)+' از '+fa(MISSIONS.length); $('#over').classList.remove('hid'); }
  function toggleMount(){
    if(P.mounted){ const h=P.mounted; P.mounted=null; hero.visible=true; const nx=h.x+Math.cos(h.yaw+1.6)*2.2, nz=h.z+Math.sin(h.yaw+1.6)*2.2; P.pos.set(nx,heightAt(nx,nz),nz); feed('پیاده شدی'); return; }
    let best=null,bd=4.2; for(const h of horses){const d=Math.hypot(h.x-P.pos.x,h.z-P.pos.z);if(d<bd){bd=d;best=h;}}
    if(best){const wasWild=best.wild; P.mounted=best;best.wild=false;hero.visible=false;sfx.neigh(); if(MS&&MS.type==='horse'&&wasWild) objProgress(1); feed(wasWild?'اسبِ وحشی رام شد!':'سوار شدی');}
  }

  function update(dt,rdt){
    P.t+=dt; dayT=(dayT+rdt/600)%1;
    const elev=Math.sin(dayT*TAU), az=Math.cos(dayT*TAU);
    sun.position.set(P.pos.x+az*320,elev*320+30,P.pos.z+90); sun.target.position.copy(P.pos);
    moon.position.set(P.pos.x-az*300,-elev*300+40,P.pos.z-80);
    const day=smooth(elev,-0.12,0.22), dusk=1-Math.abs(smooth(elev,-0.5,0.5)*2-1);
    sun.intensity=day*1.55; hemi.intensity=0.22+day*0.68; moon.intensity=(1-day)*0.45;
    const skyD=new THREE.Color(0x0a0f22), skyN=new THREE.Color(0x9fd0e8), skyK=new THREE.Color(0xd08a45);
    const sky=skyD.clone().lerp(skyN,day).lerp(skyK,dusk*0.55);
    scene.fog.color.copy(sky); scene.fog.near=130*Q.fog; scene.fog.far=920*Q.fog; scene.background=sky; starMat.opacity=1-day;
    for(const f of fires) f.li.intensity=f.b*(0.7+Math.sin(P.t*13+f.s)*0.22)*(0.55+0.75*(1-day));

    const fwd=(K.KeyW?1:0)-(K.KeyS?1:0), stf=(K.KeyD?1:0)-(K.KeyA?1:0); const wantRun=!!K.ShiftLeft;
    P.crouch=!!K.ControlLeft&&!P.mounted;
    let sp = P.mounted ? (wantRun&&P.st>1?22:11) : (P.crouch?1.7:(wantRun&&P.st>1?7.4:3.7));
    if(wantRun&&(fwd||stf)) P.st=Math.max(0,P.st-13*dt); else P.st=Math.min(100,P.st+9*dt); if(P.st<=0) sp*=0.55;
    const fx=-Math.sin(cam.yaw), fz=-Math.cos(cam.yaw), rx=-fz, rz=fx; let mx=fx*fwd+rx*stf, mz=fz*fwd+rz*stf; const ml=Math.hypot(mx,mz)||1; mx/=ml; mz/=ml;
    const k=1-Math.exp(-dt*(P.mounted?7:13)); if(fwd||stf){P.vel.x+=(mx*sp-P.vel.x)*k; P.vel.z+=(mz*sp-P.vel.z)*k;} else {P.vel.x*=Math.exp(-dt*11); P.vel.z*=Math.exp(-dt*11);}
    P.pos.x+=P.vel.x*dt; P.pos.z+=P.vel.z*dt; P.pos.x=clamp(P.pos.x,-HALF+20,HALF-20); P.pos.z=clamp(P.pos.z,-HALF+20,HALF-20);
    if(K.Space&&P.grounded&&!P.mounted){P.vY=7.5;P.grounded=false;} P.vY-=26*dt; P.pos.y+=P.vY*dt;
    const gy=heightAt(P.pos.x,P.pos.z); if(P.pos.y<=gy){ if(!P.grounded&&P.vY<-12) cam.shake+=0.2; P.pos.y=gy; P.vY=0; P.grounded=true; } else P.grounded=false;
    for(const c of colliders){ const cs=Math.cos(c.ry), sn=Math.sin(c.ry); const dx=P.pos.x-c.x, dz=P.pos.z-c.z; const lx=dx*cs-dz*sn, lz=dx*sn+dz*cs; if(Math.abs(lx)<c.hw+1&&Math.abs(lz)<c.hd+1){ const cx2=clamp(lx,-c.hw,c.hw), cz2=clamp(lz,-c.hd,c.hd); let ox=lx-cx2, oz=lz-cz2, d=Math.hypot(ox,oz); if(d<0.001){ ox=(Math.abs(lx)/c.hw>Math.abs(lz)/c.hd)?(lx>0?1:-1):0; oz=ox?0:(lz>0?1:-1); d=1; } if(d<0.95){const p=(0.95-d)/d, nlx=lx+ox*p, nlz=lz+oz*p; P.pos.x=c.x+nlx*cs+nlz*sn; P.pos.z=c.z-nlx*sn+nlz*cs; P.vel.x*=0.4;P.vel.z*=0.4;} } }
    if(P.cd>0)P.cd-=dt; if(P.reload>0){P.reload-=dt;if(P.reload<=0)finishReload();}
    if(firing&&WEPS[P.wep].auto) playerShoot(); if(firing&&!WEPS[P.wep].auto&&P.cd<=0) playerShoot();
    if(ddActive){ddTimer-=rdt; if(ddTimer<=0){ddActive=false;ddCool=12;feed('دد آی تمام شد');}} else if(ddCool>0) ddCool-=rdt; else P.dd=Math.min(100,P.dd+7*rdt);

    if(P.mounted){
      const h=P.mounted; h.x=P.pos.x; h.z=P.pos.z; h.yaw=cam.yaw+Math.PI; h.sp=Math.hypot(P.vel.x,P.vel.z);
      if(h.sp>6){ if(Math.random()<dt*9) Pdust.spawn(h.x,heightAt(h.x,h.z)+0.2,h.z,2,0.7,1.1,0.5); if(Math.random()<dt*7) sfx.hoof(); }
      P.pos.y=heightAt(P.pos.x,P.pos.z); hero.position.set(h.x,heightAt(h.x,h.z)+1.55,h.z); hero.rotation.y=h.yaw; hero.userData.armR.rotation.x=-1.5; hero.userData.armL.rotation.x=-1.5; hero.userData.hip.rotation.x=0.1;
    } else {
      const sp2=Math.hypot(P.vel.x,P.vel.z); hero.position.copy(P.pos);
      if(sp2>0.4){ const ty=Math.atan2(P.vel.x,P.vel.z); let d=ty-hero.rotation.y; while(d>Math.PI)d-=TAU; while(d<-Math.PI)d+=TAU; hero.rotation.y+=d*Math.min(1,dt*11); } else hero.rotation.y=cam.yaw;
      hero.userData.hip.rotation.x=P.crouch?0.35:0; animHuman(hero.userData,P.t,sp2,aiming&&sp2<0.5);
      if(sp2>1&&Math.random()<dt*3) Pdust.spawn(P.pos.x,P.pos.y+0.1,P.pos.z,1,0.5,0.8,0.4);
    }
    cam.recoil*=Math.exp(-dt*8); cam.shake*=Math.exp(-dt*5); cam.pitch=clamp(cam.pitch+cam.recoil*0.35,-0.5,0.95); cam.dist+=(cam.tdist-cam.dist)*Math.min(1,dt*10);
    const ty=P.pos.y+(P.mounted?3.1:(P.crouch?1.25:1.62)); const cp=Math.cos(cam.pitch);
    _v1.set(Math.sin(cam.yaw)*cp*cam.dist, Math.sin(cam.pitch)*cam.dist+0.5, Math.cos(cam.yaw)*cp*cam.dist);
    camera.position.set(P.pos.x+_v1.x, ty+_v1.y, P.pos.z+_v1.z);
    const gyc=heightAt(camera.position.x,camera.position.z)+0.9; if(camera.position.y<gyc) camera.position.y=gyc;
    const sh=cam.shake*0.5; camera.position.x+=rnd(sh,-sh); camera.position.y+=rnd(sh,-sh);
    _v2.set(P.pos.x, ty-0.1, P.pos.z); camera.lookAt(_v2);

    for(const h of horses){
      h.t+=dt;
      if(h!==P.mounted){
        if(!h.wp||Math.random()<dt*0.1) h.wp=rnd(TAU);
        if(Math.random()<dt*0.12) h.sp=rnd(5.5,1.5); else h.sp*=Math.exp(-dt*0.9);
        h.yaw+=Math.sin(h.wp+h.t*0.3)*dt*0.5;
        const s=h.sp*dt; const nx=clamp(h.x+Math.sin(h.yaw)*s,-HALF+30,HALF-30), nz=clamp(h.z+Math.cos(h.yaw)*s,-HALF+30,HALF-30); h.x=nx; h.z=nz;
      }
      const hy=heightAt(h.x,h.z); h.m.position.set(h.x,hy,h.z); h.m.rotation.y=h.yaw; animHorse(h.m.userData,h.t,h===P.mounted?h.sp:Math.min(h.sp,3));
    }
    for(const e of enemies){
      if(e.dead)continue; e.t+=dt;
      const dx=P.pos.x-e.x, dz=P.pos.z-e.z, d=Math.hypot(dx,dz);
      if(e.flash>0){e.flash-=dt;e.m.scale.setScalar(1+e.flash*1.6);}else if(e.m.scale.x!==1)e.m.scale.setScalar(1);
      if(e.state==='idle'){ if(d<46||e.alert) e.state='alert'; else e.yaw+=Math.sin(e.t*0.6+e.ph)*dt*0.4; }
      if(e.state==='alert'){ e.yaw=Math.atan2(dx,dz); if(d<70||e.t>2) e.state='chase'; }
      if(e.state==='chase'){
        e.yaw=Math.atan2(dx,dz); const want=e.kind==='boss'?16:11; const mv=d>want?1:(d<want*0.55?-1:0);
        const nx=-dz/d, nz2=dx/d, st2=Math.sin(e.t*0.8+e.ph)*0.85; const low=e.hp<e.max*0.3?-0.6:0;
        e.x+=(dx/d*(mv+low)+nx*st2)*e.sp*dt; e.z+=(dz/d*(mv+low)+nz2*st2)*e.sp*dt;
        e.x=clamp(e.x,-HALF+25,HALF-25); e.z=clamp(e.z,-HALF+25,HALF-25); e.aim-=dt;
        if(d<80&&e.aim<=0){ e.aim=rnd(2.4,1.0); const from=_v1.set(e.x,e.m.position.y+1.35,e.z); const to=_v2.set(P.pos.x,P.pos.y+1.25,P.pos.z); tracer(from,to); sfx.eshot(); Pspark.spawn(from.x,from.y,from.z,3,1,1,0.12); const acc=e.k.acc*clamp(1.15-d/130,0.25,1)*(ddActive?0.35:1)*(P.mounted?0.85:1); if(Math.random()<acc) damagePlayer(e.k.dmg*(ddActive?0.6:1)); }
        if(d>170) e.state='idle';
      }
      e.m.position.set(e.x,heightAt(e.x,e.z),e.z); e.m.rotation.y=e.yaw; animHuman(e.m.userData,e.t,e.state==='chase'?e.sp:0.3,ddActive);
    }
    for(const l of LOOT){
      if(l.dead)continue; l.t+=dt; l.m.rotation.y+=dt*1.5; l.m.position.y=l.y+Math.sin(l.t*2)*0.16;
      if(Math.hypot(l.x-P.pos.x,l.z-P.pos.z)<2.2){
        l.dead=true; scene.remove(l.m);
        if(l.type==='ammo'){P.res[0]+=12;P.res[1]+=8;sfx.reload();feed('+۱۲ فشنگ');}
        else if(l.type==='gold'){P.money+=60;sfx.coin();feed('+$'+fa(60));if(MS&&MS.type==='collect')objProgress(1);}
        else {P.hp=Math.min(P.maxHp,P.hp+45);sfx.heal();feed('جان بازیافت شد');}
      }
    }
    const msn=MS;
    if(msn){
      wpRing.rotation.z+=dt*0.8; const wd=Math.hypot(wp.x-P.pos.x,wp.z-P.pos.z);
      if(msn.type==='reach'){ if(wd<38) objProgress(1); }
      else if(msn.type==='kill'){ let alive=0; for(const e of enemies) if(!e.dead&&e.kind!=='boss'&&Math.hypot(e.homeX-wp.x,e.homeZ-wp.z)<220) alive++; prog=msn.need-alive; if(prog>=msn.need) completeMission(); }
      else if(msn.type==='boss'){ let alive=false; for(const e of enemies) if(!e.dead&&e.kind==='boss') alive=true; prog=alive?0:1; if(!alive) completeMission(); }
    } else { wpMesh.visible=wpRing.visible=false; }
    if(MS&&wpVisible) wpMesh.visible=wpRing.visible=true;
    hudT-=rdt; if(hudT<=0){hudT=0.1;drawHUD();drawMap();}
    if(subT>0){subT-=rdt;if(subT<=0)elHUD.sub.classList.add('hid');}
    if(toastT>0){toastT-=rdt;if(toastT<=0)elHUD.toast.classList.add('hid');}
    for(const f of FEED) f.a=Math.max(0.25,f.a-rdt*0.12);
    let hint=null; if(!P.mounted){for(const h of horses){if(Math.hypot(h.x-P.pos.x,h.z-P.pos.z)<3.6){hint='سوار شدن <kbd>E</kbd>';break;}}}
    if(!hint){ if(P.mag[P.wep]===0&&P.res[P.wep]>0) hint='خشاب خالی — <kbd>R</kbd>'; else if(P.res[1]>0&&P.wep===0) hint='تفنگ <kbd>2</kbd>'; else if(P.hp<35) hint='زخمی هستی — دنبالِ جعبهٔ کمک‌های اولیه بگرد'; }
    if(hint){elHUD.hint.innerHTML=hint;elHUD.hint.classList.remove('hid');} else elHUD.hint.classList.add('hid');
  }

  function updateWorld(rdt){
    for(const t of TUM){ t.m.position.x+=t.vx*t.sp*rdt; t.m.position.z+=t.vz*t.sp*rdt; t.m.rotation.x+=t.sp*rdt*2; t.m.rotation.z+=t.sp*rdt; if(Math.abs(t.m.position.x)>HALF-30)t.vx*=-1; if(Math.abs(t.m.position.z)>HALF-30)t.vz*=-1; t.m.position.y=heightAt(t.m.position.x,t.m.position.z)+0.9; }
    for(const b of BIRDS){ b.a+=b.sp*rdt; const cx=P.pos.x, cz=P.pos.z; b.g.position.set(cx+Math.cos(b.a)*b.r, heightAt(cx,cz)+b.y+Math.sin(b.a*2)*6, cz+Math.sin(b.a)*b.r); b.g.rotation.y=-b.a+Math.PI/2; b.g.children[0].rotation.z=0.35+Math.sin(b.a*9+b.ph)*0.5; b.g.children[1].rotation.z=-0.35-Math.sin(b.a*9+b.ph)*0.5; }
    dust.position.set(camera.position.x,0,camera.position.z);
    Pblood.update(rdt); Pdust.update(rdt); Pspark.update(rdt); updateTracers(rdt);
    howlT-=rdt; if(howlT<=0){ howlT=rnd(60,25); if(Math.sin(dayT*TAU)<0.05&&AC) sfx.howl(); }
    if(state!=='play'){ const t=performance.now()/1000*0.06; const r=150, cx=TOWN.x+Math.cos(t)*r, cz=TOWN.z+Math.sin(t)*r; camera.position.set(cx,heightAt(cx,cz)+22,cz); camera.lookAt(TOWN.x,TOWNY+6,TOWN.z); }
    frames++; fpsT+=rdt; if(fpsT>0.5){elHUD.fps.textContent=Math.round(frames/fpsT)+' FPS';frames=0;fpsT=0;}
  }

  function loop(now){
    requestAnimationFrame(loop);
    const rdt=Math.min((now-last)/1000,0.05); last=now;
    if(state==='play'&&!P.dead) update(rdt*(ddActive?0.32:1), rdt);
    if(window.__gameInited) updateWorld(rdt);
    if(renderer) renderer.render(scene,camera);
  }
  requestAnimationFrame(loop);

  function pause(){ if(state!=='play')return; state='pause'; document.exitPointerLock&&document.exitPointerLock(); $('#pstat').textContent='کشته‌ها: '+fa(P.kills)+'  ·  پول: $'+fa(P.money)+'  ·  کیفیت: '+['پایین','متوسط','بالا'][qk]; $('#pause').classList.remove('hid'); }
  $('#resume').onclick=()=>{ if(state!=='pause')return; $('#pause').classList.add('hid'); state='play'; requestLock(); };
  $('#togq').onclick=()=>{ setQ((qk+1)%3); $('#pstat').textContent='کیفیت: '+['پایین','متوسط','بالا'][qk]; };
  $('#restart').onclick=()=>location.reload();
  $('#revive').onclick=()=>{ P.dead=false; P.hp=P.maxHp; P.st=100; P.money=Math.max(0,P.money-100); P.pos.set(TOWN.x,heightAt(TOWN.x,TOWN.z+18),TOWN.z+18); P.vel.set(0,0,0); for(const e of enemies) if(!e.dead&&Math.hypot(e.x-TOWN.x,e.z-TOWN.z)<300) e.state='idle'; $('#over').classList.add('hid'); state='play'; requestLock(); subtitle('دکترِ شهر نجاتت داد… ۱۰۰ دلار رفت.',5); };

  globalThis.__RR={
    get P(){return P}, get MS(){return MS}, get state(){return state}, get prog(){return prog},
    get dayT(){return dayT}, cam, enemies, LOOT, horses, MISSIONS, colliders,
    scene, heightAt, shoreR, SHORE, killEnemy, damagePlayer, toggleMount, deadEye, startReload, playerShoot,
    applyQuality, startMission, spawnEnemy, setQ, objProgress, TOWN, LAKE, CAMPS
  };
  window.__startMission=startMission; window.__audioInit=audioInit; window.__feed=feed; window.__subtitle=subtitle; window.__toast=toast; window.__pause=pause;
}

/* bootstrap */
async function startGame(){
  const playBtn=$('#play'); const errEl=$('#err');
  try{
    if(!THREE){
      playBtn.textContent='در حال بارگذاری...'; playBtn.disabled=true; errEl.classList.add('hid');
      THREE=await loadThree();
      if(!THREE){
        errEl.innerHTML='بارگذاری Three.js ناموفق بود — اینترنت لازم است.<br>اگر فیلتر است VPN را روشن کن و دوباره بزن.<br><span style="font-size:12px">unpkg / jsDelivr / esm.sh / skypack / cdnjs امتحان شد</span>';
        errEl.classList.remove('hid'); playBtn.textContent='سوار شو (تلاش دوباره)'; playBtn.disabled=false; return;
      }
    }
    if(!window.__gameInited){ buildWorld(); window.__gameInited=true; last=performance.now(); }
    window.__audioInit(); $('#menu').classList.add('hid'); $('#hud').classList.remove('hid'); state='play'; P.pos.y=heightAt(P.pos.x,P.pos.z); requestLock(); window.__startMission(0); setTimeout(()=>window.__subtitle('با <kbd>Esc</kbd> مکث کن. موفق باشی، غریبه.',5),7600);
  }catch(e){ console.error(e); errEl.textContent='خطا: '+(e.message||e); errEl.classList.remove('hid'); playBtn.textContent='سوار شو (تلاش دوباره)'; playBtn.disabled=false; }
}
$('#play').onclick=startGame;
loadThree().then(m=>{ if(m) THREE=m; }).catch(()=>{});
