#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/float2.h>

namespace DotNet::Unity::Mathematics {
struct float2;
}
namespace DotNet::Unity::Mathematics {
struct float2x2;
}

namespace DotNet::Unity::Mathematics {

struct float2x2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_nD6FhZgoOnVALNm4NoUCeQ)(const ::DotNet::Unity::Mathematics::float2* c0, const ::DotNet::Unity::Mathematics::float2* c1, ::DotNet::Unity::Mathematics::float2x2* pReturnValue, void** reinteropException);
  public: static float2x2 Construct(const ::DotNet::Unity::Mathematics::float2& c0, const ::DotNet::Unity::Mathematics::float2& c1);
  private: static void (*Property_get_Item)(const ::DotNet::Unity::Mathematics::float2x2* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::float2 operator[](::std::int32_t index) const;
  public: ::DotNet::Unity::Mathematics::float2 c0;
  public: ::DotNet::Unity::Mathematics::float2 c1;
};

} // namespace DotNet::Unity::Mathematics


