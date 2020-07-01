'use strict';

import * as THREE from '../../threejs/three.module.js';

imagesURL = `${window.location.origin}/assets/js/interactive-earth/images`


function createClouds(scene, textureLoader) {
    const geometry = new THREE.SphereGeometry(6.371 + 0.02, 32, 32);
    const material = new THREE.MeshPhongMaterial({
        map: textureLoader.load(`${imagesURL}/earthcloudmap.jpg`),
        alphaMap: textureLoader.load(`${imagesURL}/earthcloudmaptransinv.jpg`),
        opacity: 0.8,
        side: THREE.DoubleSide,
        depthWrite: false,
        transparent: true
    });

    const clouds = new THREE.Mesh(geometry, material);
    scene.add(clouds);
}

function createEarth(scene, textureLoader) {
    const geometry = new THREE.SphereGeometry(6.371, 32, 32);
    const material = new THREE.MeshPhongMaterial({
        map: textureLoader.load(`${imagesURL}/8081_earthmap10k.jpg`),
        bumpMap: textureLoader.load(`${imagesURL}/8081_earthbump4k.jpg`),
        bumpScale: 0.15,
        specularMap: textureLoader.load(`${imagesURL}/8081_earthspec4k.jpg`),
        specular: 0x101010
    });

    const earth = new THREE.Mesh(geometry, material);
    scene.add(earth);

    createClouds(scene, textureLoader);
}

function createStarfield(scene, textureLoader) {
    const geometry = new THREE.SphereGeometry(1200, 32, 32);
    const material = new THREE.MeshBasicMaterial({
        color: 0xFFFFFF,
        side: THREE.BackSide,
        map: textureLoader.load(`${imagesURL}/starfield.jpg`)
    });

    const stars = new THREE.Mesh(geometry, material);
    scene.add(stars);
}

function createLight(scene, x) {
    const light = new THREE.PointLight(
        0xFFFFFF, // color
        1.5, // intensity
        2000 // drop off
    );
    light.position.set(x, 0, 0);

    scene.add(light);
}

function createSun(scene, textureLoader){
    const geometry = new THREE.SphereGeometry(2 * 0.696, 32, 32);
    const material = new THREE.MeshBasicMaterial({color: 0xFFFFFF});
    const sun = new THREE.Mesh(geometry, material);
    sun.position.x = 152;

    scene.add(sun);
    createLight(scene, sun.position.x);
}

function createScene() {
    const scene = new THREE.Scene();
    const textureLoader = new THREE.TextureLoader();

    for (let createElem of [createEarth, createStarfield, createSun]) {
        createElem(scene, textureLoader);
    }

    return scene;
}

export {createScene};