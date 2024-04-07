'use strict';

import * as THREE from '../../../threejs/three.module.js';
import { Game } from './game.js';


let renderer, camera, scene, canvas, WIDTH, HEIGHT, prevTime, game;

function initialize() {
    prevTime = 0;

    canvas = document.querySelector('#main_canvas');
    WIDTH = canvas.clientWidth;
    HEIGHT = canvas.clientHeight;

    // Default: look down the -Z axis with +Y up
    camera = new THREE.PerspectiveCamera(
        60, // FOV
        WIDTH / HEIGHT, // aspect
        0.1, // near and far clip planes
        3000
    );

    renderer = new THREE.WebGLRenderer({canvas});
    renderer.setSize(WIDTH, HEIGHT);

    canvas.addEventListener('mousemove', handleMouseMove, false);
    canvas.addEventListener('wheel', handleWheel, true);

    scene = new THREE.Scene();
    game = new Game(scene);

    requestAnimationFrame(animate);
}

function handleMouseMove(event) {
    const rect = canvas.getBoundingClientRect();
    const offsetX = rect.left;
    const offsetY = rect.left;
    const x = (event.clientX - offsetX) / WIDTH;
    const y = (event.clientY - offsetY) / HEIGHT;
    game.handleMouseMove(x, y);
}

function handleWheel(event) {
    game.handleWheel(event.deltaY);
}

function animate(time) {
    time *= 1e-3; // time in seconds
    const dt = time - prevTime;

    game.animate(time, dt);

    // Setting camera position
    const radius = 16 * game.zoom;
    camera.position.x = radius * Math.cos(game.angle);
    camera.position.z = radius * Math.sin(game.angle);
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
    requestAnimationFrame(animate);
    prevTime = time;
}


window.onload = initialize