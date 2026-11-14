uniform float uK;     // 直径の倍率（ガウシアンの σ に掛ける）
uniform float uMax;   // 大きすぎる点を抑える上限
out vec4 fragColor;
void main(){
    vec3 s = exp(texture(sTD2DInputs[0], vUV.st).rgb);
    float d = min(max(s.x, max(s.y, s.z)) * uK, uMax);
    fragColor = TDOutputSwizzle(vec4(d, d, d, 1.0));
}
