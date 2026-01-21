#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float2;
}

namespace DotNet::Unity::Mathematics {

struct float2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_aHAAcVLY3x5GFF0HQijktQ)(float x, float y, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException);
  public: static float2 Construct(float x, float y);
  private: static float (*Property_get_Item)(const ::DotNet::Unity::Mathematics::float2* thiz, ::std::int32_t index, void** reinteropException);
  public: float operator[](::std::int32_t index) const;
  public: float x;
  public: float y;
};

} // namespace DotNet::Unity::Mathematics


