uniform float uMode;    // 1＝丸い点（不透明）、2＝ぼかした点（中心ほど濃い）
uniform float uSharp;   // ぼかしの鋭さ（大きいほど中心に寄る）
in Vertex { vec4 color; vec2 uv; } iVert;
out vec4 fragColor;
void main(){
    TDCheckDiscard();
    float r2 = dot(iVert.uv, iVert.uv);
    vec3 rgb = iVert.color.rgb;
    if (uMode < 1.5) {
        if (r2 > 1.0 || iVert.color.a <= 0.15) discard;   // 箱（mat）と同じ: 不透明度 0.15 以下は描かない、色は不透明度を掛ける
        fragColor = TDOutputSwizzle(vec4(rgb * iVert.color.a, 1.0));
    } else {
        float a = exp(-r2 * uSharp) * iVert.color.a;   // 点そのものの不透明度（col_rgba の a）も掛ける
        if (a < 0.02) discard;
        fragColor = TDOutputSwizzle(vec4(rgb * a, a));   // 乗算済み
    }
}
