'use strict';

import { clamp } from './utils.js';
import { createScene } from './scene.js';


class Game {
    constructor(scene) {
        // anim. specific variables
        this.angle_v = 0;
        this.target_angle_v = 0;
        this.angle = 0;
        this.zoom = 1;

        createScene(scene);
    }

    handleMouseMove(x, y) {
        this.target_angle_v = 2.5 * (2 * x - 1);
    }

    handleWheel(deltaY) {
        const factor = 1 + 0.1 * Math.tanh(deltaY);
        this.zoom *= factor**0.3;
        this.zoom = clamp(this.zoom, 0.43, 3);
    }

    animate(time, dt) {
        const d_angle_v = 30 * dt * (this.target_angle_v - this.angle_v);
        this.angle_v += dt * d_angle_v;
        this.angle_v = clamp(this.angle_v, -2.5, 2.5);

        this.angle += dt * this.angle_v;
    }
}


export { Game };