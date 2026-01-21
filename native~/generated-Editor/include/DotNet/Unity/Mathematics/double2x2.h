#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/double2.h>

namespace DotNet::Unity::Mathematics {
struct double2;
}
namespace DotNet::Unity::Mathematics {
struct double2x2;
}

namespace DotNet::Unity::Mathematics {

struct double2x2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_N2UNoIlt5DjPRS7f8weqIA)(const ::DotNet::Unity::Mathematics::double2* c0, const ::DotNet::Unity::Mathematics::double2* c1, ::DotNet::Unity::Mathematics::double2x2* pReturnValue, void** reinteropException);
  public: static double2x2 Construct(const ::DotNet::Unity::Mathematics::double2& c0, const ::DotNet::Unity::Mathematics::double2& c1);
  private: static void (*Property_get_Item)(const ::DotNet::Unity::Mathematics::double2x2* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double2 operator[](::std::int32_t index) const;
  public: ::DotNet::Unity::Mathematics::double2 c0;
  public: ::DotNet::Unity::Mathematics::double2 c1;
};

} // namespace DotNet::Unity::Mathematics


