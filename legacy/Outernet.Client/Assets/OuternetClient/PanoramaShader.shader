Shader "Custom/PanoramaShader"
{
    Properties
    {
        _MainTex ("Panorama Texture", 2D) = "white" {}
        _Heading ("Heading", Float) = 0
        _Pitch ("Pitch", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "UnityCG.cginc"

            struct appdata_t
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float4 vertex : SV_POSITION;
            };

            sampler2D _MainTex;
            float _Heading;
            float _Pitch;

            v2f vert(appdata_t v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                return tex2D(_MainTex, frac(i.uv - 0.5 + float2(_Heading, _Pitch)));
            }
            ENDCG
        }
    }
    FallBack "Diffuse"
}
