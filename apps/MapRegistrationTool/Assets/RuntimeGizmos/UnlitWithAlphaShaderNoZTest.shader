Shader "Custom/Unlit/Unlit_Alpha_WithColor_No_ZTest" {
	Properties{
		_Color("Main Color", Color) = (1,1,1,1)
		_MainTex("Base (RGB) Trans (A)", 2D) = "white" {}
	}

		SubShader{
			Tags {"Queue" = "Transparent" "IgnoreProjector" = "True" "RenderType" = "Transparent"}

			ZWrite Off
			ZTest Off
			Lighting Off
			Fog { Mode Off }

			Blend SrcAlpha OneMinusSrcAlpha

			Pass {
				Color[_Color]
				SetTexture[_MainTex] { combine texture * primary }
			}
	}
}