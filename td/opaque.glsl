// 描いた点は不透明として扱う: 乗算済みの色を割り戻して alpha=1 にする（白地に重ねても薄くならない）
out vec4 fragColor;
void main(){
    vec4 v = texture(sTD2DInputs[0], vUV.st);
    fragColor = v.a > 0.001 ? TDOutputSwizzle(vec4(v.rgb / v.a, 1.0)) : vec4(0.0);
}
