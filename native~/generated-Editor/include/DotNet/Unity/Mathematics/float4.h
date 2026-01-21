#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float4;
}

namespace DotNet::Unity::Mathematics {

struct float4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_HRdOMAw1wcknBRlYiWJ61Q)(float x, float y, float z, float w, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException);
  public: static float4 Construct(float x, float y, float z, float w);
  private: static float (*Property_get_Item)(const ::DotNet::Unity::Mathematics::float4* thiz, ::std::int32_t index, void** reinteropException);
  public: float operator[](::std::int32_t index) const;
  public: float x;
  public: float y;
  public: float z;
  public: float w;
};

} // namespace DotNet::Unity::Mathematics


