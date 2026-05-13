Shader "Custom/URP/PointCloud"
{
    Properties
    {
        _PointSize ("Point Size", Float) = 10.0
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline"="UniversalPipeline"
            "RenderType"="Opaque"
            "Queue"="Geometry"
        }

        Pass
        {
            Name "PointCloud"

            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite On
            Cull Off

            HLSLPROGRAM

            #pragma target 5.0
            #pragma vertex Vert
            #pragma geometry Geom
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float3 positionOS : POSITION;
                float4 color : COLOR;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float4 color : COLOR;
            };

            CBUFFER_START(UnityPerMaterial)
                float _PointSize;
            CBUFFER_END

            Varyings Vert(Attributes input)
            {
                Varyings o;

                VertexPositionInputs posInputs =
                    GetVertexPositionInputs(input.positionOS);

                o.positionCS = posInputs.positionCS;
                o.color = input.color;

                return o;
            }

            [maxvertexcount(6)]
            void Geom(
                point Varyings input[1],
                inout TriangleStream<Varyings> triStream)
            {
                float4 center = input[0].positionCS;
                float4 color = input[0].color;

                // Convert pixel size to clip-space offset
                float2 pixelSize =
                    (_PointSize / _ScreenParams.xy) * 2.0;

                float2 offsets[4] =
                {
                    float2(-1, -1),
                    float2(-1,  1),
                    float2( 1,  1),
                    float2( 1, -1)
                };

                Varyings o;

                // Triangle 1
                o.color = color;

                o.positionCS = center;
                o.positionCS.xy += offsets[0] * pixelSize * center.w;
                triStream.Append(o);

                o.positionCS = center;
                o.positionCS.xy += offsets[1] * pixelSize * center.w;
                triStream.Append(o);

                o.positionCS = center;
                o.positionCS.xy += offsets[2] * pixelSize * center.w;
                triStream.Append(o);

                triStream.RestartStrip();

                // Triangle 2
                o.positionCS = center;
                o.positionCS.xy += offsets[0] * pixelSize * center.w;
                triStream.Append(o);

                o.positionCS = center;
                o.positionCS.xy += offsets[2] * pixelSize * center.w;
                triStream.Append(o);

                o.positionCS = center;
                o.positionCS.xy += offsets[3] * pixelSize * center.w;
                triStream.Append(o);

                triStream.RestartStrip();
            }

            half4 Frag(Varyings input) : SV_Target
            {
                return input.color;
            }

            ENDHLSL
        }
    }
}