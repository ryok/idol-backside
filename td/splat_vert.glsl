// 点を板（カメラに正対する四角）で描く。pt_style 1＝丸い点、2＝ぼかした点（ガウシアン）
// 板の大きさは、箱で描くときと同じインスタンスの大きさ（scale_size）× uSize
uniform float uSize;
out Vertex { vec4 color; vec2 uv; } oVert;
void main(){
    vec4 c = TDDeform(vec3(0.0));
    float s = length(TDDeform(vec3(1.0, 0.0, 0.0)).xyz - c.xyz);   // インスタンスの大きさ
    vec4 camC = uTDMats[TDCameraIndex()].cam * c;
    camC.xy += P.xy * s * uSize;
    gl_Position = uTDMats[TDCameraIndex()].proj * camC;
    oVert.uv = P.xy * 2.0;   // -1〜1
    oVert.color = TDInstanceColor(Cd);
}
