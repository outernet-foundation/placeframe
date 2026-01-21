#include <DotNet/Unity/Mathematics/double2x2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/double2.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double2;
}
namespace DotNet::Unity::Mathematics {
struct double2x2;
}

namespace DotNet::Unity::Mathematics {

void (*double2x2::Construct_N2UNoIlt5DjPRS7f8weqIA)(const ::DotNet::Unity::Mathematics::double2* c0, const ::DotNet::Unity::Mathematics::double2* c1, ::DotNet::Unity::Mathematics::double2x2* pReturnValue, void** reinteropException) = nullptr;


double2x2 double2x2::Construct(const ::DotNet::Unity::Mathematics::double2& c0, const ::DotNet::Unity::Mathematics::double2& c1)
{
    void* reinteropException = nullptr;
    double2x2 result;
    Construct_N2UNoIlt5DjPRS7f8weqIA(&c0, &c1, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::Unity::Mathematics::double2x2::Property_get_Item)(const ::DotNet::Unity::Mathematics::double2x2* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double2 double2x2::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double2 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


