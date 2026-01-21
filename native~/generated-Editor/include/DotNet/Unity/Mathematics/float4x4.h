#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/float4.h>

namespace DotNet::Unity::Mathematics {
struct float4;
}
namespace DotNet::Unity::Mathematics {
struct float4x4;
}

namespace DotNet::Unity::Mathematics {

struct float4x4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_40mXKMXvvkbHdnVEuqJdsw)(const ::DotNet::Unity::Mathematics::float4* c0, const ::DotNet::Unity::Mathematics::float4* c1, const ::DotNet::Unity::Mathematics::float4* c2, const ::DotNet::Unity::Mathematics::float4* c3, ::DotNet::Unity::Mathematics::float4x4* pReturnValue, void** reinteropException);
  public: static float4x4 Construct(const ::DotNet::Unity::Mathematics::float4& c0, const ::DotNet::Unity::Mathematics::float4& c1, const ::DotNet::Unity::Mathematics::float4& c2, const ::DotNet::Unity::Mathematics::float4& c3);
  private: static void (*Property_get_Item)(const ::DotNet::Unity::Mathematics::float4x4* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::float4 operator[](::std::int32_t index) const;
  public: ::DotNet::Unity::Mathematics::float4 c0;
  public: ::DotNet::Unity::Mathematics::float4 c1;
  public: ::DotNet::Unity::Mathematics::float4 c2;
  public: ::DotNet::Unity::Mathematics::float4 c3;
};

} // namespace DotNet::Unity::Mathematics


