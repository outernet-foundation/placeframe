#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float3;
}

namespace DotNet::Unity::Mathematics {

struct float3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_LB__scTJntm1swre2IwXuIw)(float x, float y, float z, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException);
  public: static float3 Construct(float x, float y, float z);
  private: static float (*Property_get_Item)(const ::DotNet::Unity::Mathematics::float3* thiz, ::std::int32_t index, void** reinteropException);
  public: float operator[](::std::int32_t index) const;
  public: float x;
  public: float y;
  public: float z;
};

} // namespace DotNet::Unity::Mathematics


