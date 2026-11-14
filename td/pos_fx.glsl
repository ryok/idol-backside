// 音で点を崩す。入力0 = 位置（ply_pos）
// 低音(uBass)で全体が膨らむ。打音(uHit)で点がそれぞれの向きへ散る。
// uBackOnly=1 のとき、散るのは「写真に写っていなかった側」の点だけ（写っていた正面は崩れない）
uniform float uBass;
uniform float uHit;
uniform float uTime;
uniform float uBassAmt;
uniform float uHitAmt;
uniform float uBackOnly;
uniform vec3 uSeen;   // 入力カメラの向き（点群のローカル座標）
out vec4 fragColor;
vec3 hash3(vec2 p){
    vec3 q = vec3(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)), dot(p, vec2(419.2, 371.9)));
    return fract(sin(q) * 43758.5453);
}
void main(){
    vec4 v = texture(sTD2DInputs[0], vUV.st);
    vec3 p = v.xyz;
    // 写っていた度合い: 入力カメラの方を向いている点ほど 1
    float facing = dot(normalize(p + 1e-6), normalize(uSeen));
    float hidden = 1.0 - smoothstep(-0.2, 0.4, facing);
    float w = mix(1.0, hidden, uBackOnly);
    p *= 1.0 + uBass * uBassAmt;
    vec3 dir = normalize(hash3(vUV.st * 512.0) * 2.0 - 1.0);
    vec3 jit = hash3(vUV.st * 512.0 + floor(uTime * 12.0)) - 0.5;
    p += (dir + jit * 0.5) * uHit * uHitAmt * w;
    fragColor = TDOutputSwizzle(vec4(p, v.a));
}
