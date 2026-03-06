/**
 * Utility to standardize MediaPipe Pose landmarks into a fixed 768-dimensional vector.
 * Mirroring the logic from backend/app/core/feature_extractor.py
 */

export interface Landmark {
    x: number;
    y: number;
    z: number;
    visibility: number;
}

export class PoseStandardizer {
    static readonly TARGET_DIM = 768;

    /**
     * Calculates the angle between three 3D points.
     */
    static calculateAngle(a: Landmark, b: Landmark, c: Landmark): number {
        const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
        let angle = Math.abs((radians * 180.0) / Math.PI);
        if (angle > 180.0) angle = 360.0 - angle;
        return angle;
    }

    /**
     * Standardizes raw landmarks into a unit-normalized 768d vector.
     */
    static standardize(landmarks: Landmark[]): number[] {
        if (landmarks.length < 33) return new Array(this.TARGET_DIM).fill(0);

        const angles: number[] = [];

        // 1. Calculate Key Joint Angles
        try {
            // Left Elbow: 11, 13, 15
            angles.push(this.calculateAngle(landmarks[11], landmarks[13], landmarks[15]));
            // Right Elbow: 12, 14, 16
            angles.push(this.calculateAngle(landmarks[12], landmarks[14], landmarks[16]));
            // Left Shoulder: 13, 11, 23
            angles.push(this.calculateAngle(landmarks[13], landmarks[11], landmarks[23]));
            // Right Shoulder: 14, 12, 24
            angles.push(this.calculateAngle(landmarks[14], landmarks[12], landmarks[24]));
            // Left Hip: 11, 23, 25
            angles.push(this.calculateAngle(landmarks[11], landmarks[23], landmarks[25]));
            // Right Hip: 12, 24, 26
            angles.push(this.calculateAngle(landmarks[12], landmarks[24], landmarks[26]));
            // Left Knee: 23, 25, 27
            angles.push(this.calculateAngle(landmarks[23], landmarks[25], landmarks[27]));
            // Right Knee: 24, 26, 28
            angles.push(this.calculateAngle(landmarks[24], landmarks[26], landmarks[28]));
        } catch (e) {
            console.warn("Failed to calculate some angles", e);
        }

        // 2. Flatten raw landmarks (x, y, z) + visibility -> 132 values
        const flattened: number[] = [];
        landmarks.forEach(lm => {
            flattened.push(lm.x, lm.y, lm.z, lm.visibility);
        });

        // 3. Concatenate and Pad
        const rawVector = [...angles, ...flattened];
        let standardizedVector = new Array(this.TARGET_DIM).fill(0);

        for (let i = 0; i < Math.min(rawVector.length, this.TARGET_DIM); i++) {
            standardizedVector[i] = rawVector[i];
        }

        // 4. Unit Normalization (L2 Norm)
        const squaredSum = standardizedVector.reduce((acc, val) => acc + val * val, 0);
        const norm = Math.sqrt(squaredSum);

        if (norm > 0) {
            standardizedVector = standardizedVector.map(val => val / norm);
        }

        return standardizedVector;
    }
}
