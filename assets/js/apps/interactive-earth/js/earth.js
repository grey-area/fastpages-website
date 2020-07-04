'use strict';

import * as THREE from '../../../threejs/three.module.js';
import {createScene} from './scene.js';


let renderer, canvas, camera, scene, WIDTH;
let prevTime = 0;
let angle_v = 0;
let target_angle_v = 0;
let angle = 0;
let zoom = 1;


function initialize() {
    canvas = document.querySelector('#main_canvas');

    // Default: look down the -Z axis with +Y up
    camera = new THREE.PerspectiveCamera(
        60, // FOV
        canvas.clientWidth / canvas.clientHeight, // aspect
        0.1, // near and far clip planes
        3000
    );

    WIDTH = canvas.clientWidth;

    renderer = new THREE.WebGLRenderer({canvas});
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);

    canvas.addEventListener('mousemove', handleMouseMove, false);
    canvas.addEventListener('wheel', handleWheel, true);

    scene = createScene();

    requestAnimationFrame(animate);
}

function clamp(x, lo, hi) {
    return Math.max(lo, Math.min(hi, x));
}

function handleMouseMove(event) {
    const rect = canvas.getBoundingClientRect();
    const offsetX = rect.left;

    target_angle_v = 2.5 * (2 * ((event.clientX - offsetX) / WIDTH) - 1);
}

function handleWheel(event) {
    const factor = 1 + 0.1 * Math.tanh(event.deltaY);
    zoom *= factor**0.3;
    zoom = clamp(zoom, 0.43, 3);
}

function animate(time) {
    time *= 1e-3; // time in seconds
    const dt = time - prevTime;

    const d_angle_v = 30 * dt * (target_angle_v - angle_v);
    angle_v += dt * d_angle_v;
    angle_v = clamp(angle_v, -2.5, 2.5);

    angle += dt * angle_v;

    // TODO temporary camera control
    const radius = 16 * zoom;
    camera.position.x = radius * Math.cos(angle);
    camera.position.z = radius * Math.sin(angle);
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
    requestAnimationFrame(animate);
    prevTime = time;
}


window.onload = initialize