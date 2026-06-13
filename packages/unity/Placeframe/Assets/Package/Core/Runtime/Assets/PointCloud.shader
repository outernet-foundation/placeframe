Shader "Placeframe/PointCloud"
{
    Properties
    {
        _PointSize ("Point Size (m)", Float) = 0.02
        [HDR] _Tint ("Tint", Color) = (1, 1, 1, 1)
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Opaque"
            "Queue" = "Geometry"
        }

        Pass
        {
            Name "PointCloud"

            ZWrite On
            Cull Off

            HLSLPROGRAM

            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float3 centerOS : POSITION;
                float2 corner : TEXCOORD0;
                half4 color : COLOR;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                half4 color : COLOR;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            CBUFFER_START(UnityPerMaterial)
                float _PointSize;
                half4 _Tint;
            CBUFFER_END

            Varyings Vert(Attributes input)
            {
                Varyings output = (Varyings)0;

                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);

                // Billboard in view space so each point is a constant-size,
                // screen-facing quad: offset the center by the corner in metres,
                // then project. _PointSize is the quad half-extent in metres.
                float3 positionWS = TransformObjectToWorld(input.centerOS);
                float3 positionVS = TransformWorldToView(positionWS);
                positionVS.xy += input.corner * _PointSize;

                output.positionCS = TransformWViewToHClip(positionVS);
                output.color = input.color * _Tint;

                return output;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                return input.color;
            }

            ENDHLSL
        }
    }
}
