Shader "ExtrudedText/Unlit"
{
	Properties
	{
		// General
		_FaceTex("Face Texture", 2D) = "white" {}
		_Color("Color", Color) = (1,1,1,1)
		_WeightBold("Weight Bold", Range(0,1)) = 0.6
		_WeightNormal("Weight Normal", Range(0,1)) = 0.5

		// 3D
		_RaymarchMinStep("Raymarch min step", Range(0.001, 0.1)) = 0.01
		_RaymarchStepLength("Raymarch step length", Range(0.001, 1)) = 0.1
		_RaymarchBlueNoise("Raymarch Blue Noise", 2DArray) = "black" {}
		_RaymarchBlueNoise_Slices("Raymarch Blue Noise Slices", float) = 1
		_RaymarchBlueNoise_Speed("Raymarch Blue Noise Speed", float) = 10
		_RaymarchTemporalStepLength("Raymarch Temporal Step Length", Vector) = (0.01, 0.05, 0, 0)
		_DepthAlbedo("Depth Albedo", 2D) = "white" {}

		// Outline
		_OutlineColor("Outline Color", Color) = (0,0,0,1)
		_OutlineWidth("Outline Thickness", Range(0,1)) = 0
		_OutlineSoftness("Outline Softness", Range(0,1)) = 0

		// Font Atlas properties
		_MainTex("Font Atlas", 2D) = "white" {}
		_TextureWidth("Texture Width", float) = 512
		_TextureHeight("Texture Height", float) = 512
		_GradientScale("Gradient Scale", float) = 5.0
		_ScaleX("Scale X", float) = 1.0
		_ScaleY("Scale Y", float) = 1.0
		_PerspectiveFilter("Perspective Correction", Range(0, 1)) = 0.875
		_Sharpness("Sharpness", Range(-1,1)) = 0

		// TMP INTERNAL
		_ScaleRatioA("Scale Ratio A", float) = 1.0
		_ScaleRatioB("Scale Ratio B", float) = 1.0
		_ScaleRatioC("Scale Ratio C", float) = 1.0
	}
	SubShader
	{
		Tags
		{
			"Queue" = "Geometry"
			"IgnoreProjector" = "True"
			"RenderType" = "Geometry"
		}

		Cull Off
		
		Lighting Off
		Fog { Mode Off }

		Pass
		{
			Stencil
			{
				Ref 2
				Comp Always
				Pass Replace
			}

			CGPROGRAM
			#pragma target 3.0
			#pragma vertex TMP3D_VERT
			// #pragma geometry TMP3D_GEOM_VARIANT
			#pragma fragment TMP3D_FRAG_UNLIT

			#pragma multi_compile _MAXSTEPS_32 _MAXSTEPS_64 _MAXSTEPS_96 _MAXSTEPS_128
			#pragma multi_compile __ DEBUG_STEPS DEBUG_MASK

			// #pragma require geometry

			#include "UnityCG.cginc"
			
			// General
			uniform sampler2D   _FaceTex;
			fixed4				_Color;
			uniform float		_WeightBold;
			uniform float 		_WeightNormal;

			// 3D
			sampler2D _DepthAlbedo;

			// Outline
			uniform fixed4		_OutlineColor;
			uniform float		_OutlineWidth;

			// Font Atlas properties
			uniform sampler2D	_MainTex;
			uniform float		_TextureWidth;
			uniform float		_TextureHeight;
			uniform float 		_GradientScale;

			// Raymarch
			float _RaymarchMinStep;

			// Used by Unity internally to handle Texture Tiling and Offset.
			float4 _MainTex_TexelSize;
			float4 _FaceTex_ST;

			// TMP INTERNAL
			uniform float		_ScaleRatioA;
			uniform float		_ScaleRatioB;
			uniform float		_ScaleRatioC;

			struct tmp3d_a2v {
				UNITY_VERTEX_INPUT_INSTANCE_ID
				float4	position		: POSITION;
				float3	normal			: NORMAL;
				fixed4	color			: COLOR;
				float2	style			: TEXCOORD1;
				float3	depth			: TEXCOORD2;
				float4  quadUVBounds	: TEXCOORD3;
				float4  quadBounds		: TEXCOORD4;
				float2  skew			: TEXCOORD5;
			};
			
			struct tmp3d_g2f {
				UNITY_VERTEX_INPUT_INSTANCE_ID
				float4	position			: SV_POSITION;
				fixed4	color				: COLOR;
				float4	worldPos			: TEXCOORD1;
				float2	style				: TEXCOORD6;
				float3	depth				: TEXCOORD5;
				float4	quadUVBounds		: TEXCOORD2;
				float4	quadBounds		    : TEXCOORD3;
				float	skew		       	: TEXCOORD4;
			};

			tmp3d_g2f TMP3D_VERT(tmp3d_a2v input)
			{
				tmp3d_g2f output;

				output.worldPos = mul(unity_ObjectToWorld, input.position);
				output.position = UnityObjectToClipPos(input.position);
				output.color = input.color;
				output.style = input.style;
				output.depth = input.depth;
				output.quadUVBounds = input.quadUVBounds;
				output.quadBounds = input.quadBounds;
				output.skew = input.skew;

				return output;
			}

			#if _MAXSTEPS_32
			#define MAX_STEPS 32
			#elif _MAXSTEPS_64
			#define MAX_STEPS 64
			#elif _MAXSTEPS_96
			#define MAX_STEPS 96
			#elif _MAXSTEPS_128
			#define MAX_STEPS 128
			#else
			#define MAX_STEPS 16
			#endif

			struct fragOutput
			{
				fixed4 color : SV_Target;
				float depth : SV_Depth;
			};

			float InverseLerp(float a, float b, float x)
			{
				return (x - a) * (1 / (b - a));
			}

			fragOutput TMP3D_FRAG_UNLIT(tmp3d_g2f input)
			{
				UNITY_SETUP_INSTANCE_ID(input);

				fragOutput output;
				output.depth = 0;
				output.color = 0;

				float isBold = step(input.style.y, 0);
				float edgeThreshold = lerp(_WeightNormal, _WeightBold, isBold);

				float characterDepth = input.depth.x;
				float2 characterDepthMapped = input.depth.yz;

				float3 viewDirection = normalize(input.worldPos.xyz - _WorldSpaceCameraPos.xyz);
				viewDirection = lerp(viewDirection, normalize(mul((float3x3)unity_CameraToWorld, float3(0, 0, 1))), unity_OrthoParams.w);

				// Transform the starting position to object space
				float3 localStartPosition = mul(unity_WorldToObject, float4(input.worldPos.xyz, 1));

				// Extract rotation-only matrix from unity_ObjectToWorld
				float3x3 objectToWorld = (float3x3)unity_ObjectToWorld;

				// Normalize the columns to remove scaling and get the rotation matrix
				float3x3 worldToLocalRotation;
				worldToLocalRotation[0] = normalize(objectToWorld[0]);
				worldToLocalRotation[1] = normalize(objectToWorld[1]);
				worldToLocalRotation[2] = normalize(objectToWorld[2]);

				// Get the inverse (transpose) of the rotation matrix to transform from world to object space
				float3x3 worldToObjectRotation = transpose(worldToLocalRotation);

				// Transform the view direction to object space without scaling
				float3 objectSpaceviewDirection = mul(worldToObjectRotation, viewDirection);

				float raymarchProgress = 0;

				for (int step = 0; step <= MAX_STEPS; step++)
				{
					float3 localRayPosition = localStartPosition + objectSpaceviewDirection * raymarchProgress;

					// Compute normalized texture coordinates for ray position within bounding box
					float normalizedY = InverseLerp(input.quadBounds.y, input.quadBounds.y + input.quadBounds.w, localRayPosition.y);
					float xOffset = saturate(normalizedY) * input.skew;
					float normalizedX = InverseLerp(input.quadBounds.x, input.quadBounds.x + input.quadBounds.z, localRayPosition.x - xOffset);
					float normalizedZ = InverseLerp(-characterDepth, 0, localRayPosition.z);
					float3 normalizedRayPosition = float3(normalizedX, normalizedY, normalizedZ);

					 // Compute soft clipping bounds
					float clipX = -(abs(normalizedRayPosition.x - 0.5) - 0.5) + 0.01;
					float clipY = -(abs(normalizedRayPosition.y - 0.5) - 0.5) + 0.01;
					float clipZ = -(abs(normalizedRayPosition.z - 0.5) - 0.5) + 0.01;
					float boundingClip = min(0, min(clipX, min(clipY, clipZ)));
	
					normalizedRayPosition = saturate(normalizedRayPosition);
					float2 textureUV = float2(
						saturate(lerp(input.quadUVBounds.x, input.quadUVBounds.x + input.quadUVBounds.z, normalizedRayPosition.x)),
						saturate(lerp(input.quadUVBounds.y, input.quadUVBounds.y + input.quadUVBounds.w, normalizedRayPosition.y))
					);

					float4 textureSample = tex2Dlod(_MainTex, float4(textureUV, 0, 0));
					float signedDistanceField = 1 - textureSample.a;
	
					// Compute gradient scaling for proper edge representation
					float gradientPixelSize = _GradientScale / _TextureHeight;
					float gradientRelativeScale = gradientPixelSize / input.quadUVBounds.w;
					float adjustedGradient = input.quadBounds.w * gradientRelativeScale;
	
					float minimum = -(adjustedGradient * edgeThreshold);
					float maximum = adjustedGradient * (1 - edgeThreshold);
					float sdfThreshold = lerp(minimum, maximum, signedDistanceField);
	
					// Compute intersection step size along the ray
					float horizontalMagnitude = length(objectSpaceviewDirection.xy);
					float intersectionStep = sdfThreshold / horizontalMagnitude;
	
					raymarchProgress += max(length(objectSpaceviewDirection) * intersectionStep, _RaymarchMinStep);

					clip(boundingClip);

					// If within threshold, determine final color and depth
					if (signedDistanceField <= edgeThreshold)
					{
						float objectDepth = -localRayPosition.z;
						float depthFactor = saturate(InverseLerp(0, characterDepth, objectDepth));
						depthFactor = saturate(lerp(characterDepthMapped.x, characterDepthMapped.y, depthFactor));

						float3 baseColor = tex2Dlod(_DepthAlbedo, float4(depthFactor, 0.5, 0, 0)).rgb * _Color.rgb;
						float2 faceTextureUV = localRayPosition.xy * _FaceTex_ST.xy - _FaceTex_ST.zw;
						float3 faceColor = tex2Dlod(_FaceTex, float4(faceTextureUV, 0, 0)).rgb;
						baseColor *= faceColor;

						float4 clipPosition = UnityObjectToClipPos(localRayPosition);
						#if defined(SHADER_TARGET_GLSL) || defined(SHADER_API_GLES) || defined(SHADER_API_GLES3)
						output.depth = ((clipPosition.z / clipPosition.w) + 1.0) * 0.5;
						#else
						output.depth = clipPosition.z / clipPosition.w;
						#endif

						output.color = float4(baseColor.rgb * input.color, 1);
						
						return output;
					}
				}

				clip(-1);

				return output;
			}

			ENDCG
		}
	}
	CustomEditor "Outernet.Client.ExtrudedTextUnlitShaderGUI"
}
