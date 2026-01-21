#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/double3.h>

namespace DotNet::Unity::Mathematics {
struct double3;
}
namespace DotNet::Unity::Mathematics {
struct double3x3;
}

namespace DotNet::Unity::Mathematics {

struct double3x3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_qgf8OQh32bnPxjj_codUtg)(const ::DotNet::Unity::Mathematics::double3* c0, const ::DotNet::Unity::Mathematics::double3* c1, const ::DotNet::Unity::Mathematics::double3* c2, ::DotNet::Unity::Mathematics::double3x3* pReturnValue, void** reinteropException);
  public: static double3x3 Construct(const ::DotNet::Unity::Mathematics::double3& c0, const ::DotNet::Unity::Mathematics::double3& c1, const ::DotNet::Unity::Mathematics::double3& c2);
  private: static void (*Property_get_Item)(const ::DotNet::Unity::Mathematics::double3x3* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double3 operator[](::std::int32_t index) const;
  public: ::DotNet::Unity::Mathematics::double3 c0;
  public: ::DotNet::Unity::Mathematics::double3 c1;
  public: ::DotNet::Unity::Mathematics::double3 c2;
};

} // namespace DotNet::Unity::Mathematics


