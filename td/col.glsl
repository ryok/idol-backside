out vec4 fragColor;
void main(){
    vec4 v = texture(sTD2DInputs[0], vUV.st);
    vec3 rgb = clamp(0.5 + 0.28209479 * v.rgb, 0.0, 1.0);
    float a = 1.0 / (1.0 + exp(-v.a));
    fragColor = TDOutputSwizzle(vec4(rgb, a));
}
