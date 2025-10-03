Shader "Plerion/Point Cloud"
{
	Properties
	{
		_PointSize("Point Size", Range(0.1, 10)) = 1
		_PointColor("Point Color", Color) = (1, 1, 1, 1)
	}

	SubShader
	{
		Cull Off
		Tags{ "RenderType" = "Opaque" }
		LOD 100

		Pass
		{
			CGPROGRAM
			#pragma target 3.0
			#pragma vertex vert
			#pragma fragment frag

			#include "UnityCG.cginc"

			float _PointSize;
			fixed4 _PointColor;

			struct appdata
			{
				float3 vertex : POSITION;
			};

			struct v2f
			{
				float psize : PSIZE;
				float4 center : TEXCOORD0;
				half size : TEXCOORD1;
			};

			v2f vert(appdata v, out float4 outpos : SV_POSITION)
			{
				v2f o;
				outpos = UnityObjectToClipPos(v.vertex);
				o.center = ComputeScreenPos(outpos);
                o.psize = lerp(_PointSize, _PointSize / outpos.w * _ScreenParams.y, step(0.5, 1));
				o.size = o.psize;
				return o;
			}
            
			fixed4 frag (v2f i, UNITY_VPOS_TYPE vpos : VPOS) : SV_Target
            {
                if (distance(vpos.xy, i.center.xy / i.center.w * _ScreenParams.xy) > i.size * 0.5) discard;
                return _PointColor;
            }
			ENDCG
		}
	}
}