/* Lightweight Three.js hero object. It only mounts when a hero canvas exists. */
(() => {
  const canvas = document.getElementById('heroParticles');
  if (!canvas || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js';
  script.onload = () => {
    if (!window.THREE) return;
    const THREE = window.THREE;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, .1, 100);
    camera.position.z = 7;
    const renderer = new THREE.WebGLRenderer({canvas, alpha:true, antialias:true});
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
    const resize = () => { const r=canvas.getBoundingClientRect(); renderer.setSize(r.width,r.height,false); camera.aspect=r.width/r.height; camera.updateProjectionMatrix(); };
    resize(); window.addEventListener('resize',resize);
    const group = new THREE.Group();
    const geo = new THREE.IcosahedronGeometry(1.55,1);
    const mat = new THREE.MeshBasicMaterial({color:0xd6aa45,wireframe:true,transparent:true,opacity:.45});
    const mesh = new THREE.Mesh(geo,mat); group.add(mesh);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(2.0,.025,12,96), new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:.28}));
    ring.rotation.x = Math.PI/2.4; group.add(ring);
    scene.add(group);
    const dots = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({color:0xf3d98c,size:.025,transparent:true,opacity:.8}));
    const arr=[]; for(let i=0;i<280;i++){const a=Math.random()*Math.PI*2,b=Math.acos(2*Math.random()-1),r=2.4+Math.random()*1.2;arr.push(r*Math.sin(b)*Math.cos(a),r*Math.sin(b)*Math.sin(a),r*Math.cos(b));}
    dots.geometry.setAttribute('position',new THREE.Float32BufferAttribute(arr,3)); scene.add(dots);
    const mouse={x:0,y:0}; window.addEventListener('pointermove',e=>{mouse.x=(e.clientX/innerWidth-.5)*.3;mouse.y=(e.clientY/innerHeight-.5)*.2},{passive:true});
    const animate=()=>{group.rotation.y+=.0028;group.rotation.x+=.0012;group.position.x+=(mouse.x-group.position.x)*.03;group.position.y+=(-mouse.y-group.position.y)*.03;dots.rotation.y-=.0007;renderer.render(scene,camera);requestAnimationFrame(animate)}; animate();
  };
  document.head.appendChild(script);
})();
